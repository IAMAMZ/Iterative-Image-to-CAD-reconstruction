# Stage 1 pipeline — technical overview

How a Fusion360 part goes from a ground-truth mesh, through cadrille's predicted program, through
rounds of agent edits, to the tables and figures. Covers every core file and what it writes.

## 1. The idea in one paragraph

A vision-language agent edits a CadQuery program round by round so that its solid matches a set
of target pictures. Round 0 is cadrille's prediction. Each round the agent sees the target views,
the current candidate's views and (depending on the *arm*) extra evidence; it returns an edited
program; the program is built and rendered with the same cameras; then a rule decides whether the
edit is kept. The arms differ in evidence and in that rule — VLM visual review, our
ground-truth-free forward-rendering geometric check, or both. The hidden 3D shape is used only
afterwards, to label every edit as beneficial / neutral / harmful and to score the runs.

Our three contributions relative to CADCodeVerify and GATOR:
1. a **local open-weight VLM** as the agent (both papers use proprietary models);
2. a **GT-free geometric checker** that informs the edit and gates acceptance, with **view weights**
   that down-weight target views which disagree with the others;
3. **CAD-kernel diagnostics** (per-operation OpenCascade checks, no-op / split warnings) fed back
   to the agent, also when the build succeeds.

The main method is the `geo` arm (arm names are unchanged; "main method" / "ablation" are
labels only): the geometric checker alone informs and gates every edit. `hybrid`
(geo + CADCodeVerify-style verification questions and VLM judge) is an ablation that asks whether
adding visual review on top helps; on the pilot it did not (all-Yes stops ended runs early, the
judge vetoed a good edit).

## 2. Data flow

```
cadrille/results/fusion360_test_gt/<part>.stl        cadrille/work_dirs/f360_rl_test/py/<part>.py
   (GT mesh, unit cube)                                (cadrille's predicted program)  + scores.json
          │                                                          │
          │  cadrille_init.py split  ──► data/fusion360/stage1.txt (+ stage1_meta.json)
          ▼                                                          │
 data/fusion360_targets.py                                           ▼
   map to cadrille frame, render 4 cameras            cadrille_init.py convert --tag rl
          │                                             append `result = r`, build, fit scale
          ▼                                                          │
 data/generated/targets/fusion360/<part>/                           ▼
   renders/  internal/{depth.npz,info.json}  gt.stl   data/generated/init/cadrille_rl/<part>.py
          │                                                          │
          └───────────────────────┬──────────────────────────────────┘
                                  ▼
                      refine.py  (per part, per arm, N rounds)
                        agent (vlm.py) ─ build (generate_solid.py + op_checker.py)
                        ─ compare (compare.py) ─ accept (geo_check.py / judge)
                        ─ offline score (eval3d.py)
                                  │
                                  ▼
                      runs/<date>_<name>/parts/<part>/<arm>/round_XX_<outcome>/
                                  │
                report.py (summarize_runs.py + figures.py), after every part
                README.md  results.md  results/  parts/<part>/{compare.png,scores.md}
```

Commands (the README has the same):

```sh
uv run python cadrille_init.py split
uv run python data/fusion360_targets.py
uv run python cadrille_init.py convert --tag rl
uv run python refine.py data/generated/targets/fusion360/* \
    --init data/generated/init/cadrille_rl --arm main --rounds 4 --name stage1
# -> runs/<date>_stage1/README.md   (report.py runs/<run> rebuilds the pages)
```

The default backend is `vertex` (Gemini on Vertex AI): `cp .env.example .env`, set
`GOOGLE_CLOUD_PROJECT` and `VERTEX_MODEL`, then `gcloud auth application-default login` once.
`--backend ollama` uses the local model (default `--model gemma4:12b`; pass the one you have
pulled). `--backend echo` replaces the model with a fake agent for dry runs.

## 3. Frames and units

- **cadrille frame.** cadrille writes programs centred on the bounding box with the longest side ≈ 200.
  The GT meshes are in the unit cube, so `data/fusion360_targets.py` maps them with
  `x = (x_gt − 0.5) · 200`. Target and cadrille program are then in the same frame with no fitting.
  Lengths shown to the agent are "units", not mm.
- **Render frame.** `rig.normalize` scales a mesh into a unit bounding sphere for rendering.
  A target stores its `normalization` (centre, scale) in `info.json`; candidates are rendered with
  `--like <target>` so they use the *same* normalisation and therefore the same pixels-per-unit.
- **Centring.** Candidates are built with `--center-at` = the target's bbox centre (measured from the
  target's depth maps, `view_weights.measure_bbox`). This forgives translation errors (known limit).

## 4. Core files

### Building and rendering

| File | Role |
|---|---|
| `rig.py` | The 4 fixed cameras `top_front top_right top_back top_left`: 45° above the table, 90° apart, as in RealCAD (one phone camera, part turned between photos; VGGT on test50 gives a median elevation of 43°). Same directions as `data/cameras.json`. The agent sees all 4 as its 2×2 grid; the checker and view weights use the same 4; the underside is never seen. 512×512, 40° FOV, distance 3.5 (unit sphere fills ~85% of the frame). Runs before 2026-11-24 used 8 cameras (`front back right left top bottom iso_fr iso_bl`; agent grid `front right top iso_fr`); their targets are in `data/generated/targets/*_8view`. Saves/loads `rig.json` (OpenGL camera-to-world). `normalize()` and `render_rig()`. |
| `cq_render.py` | `CQRenderer` (pyrender, offscreen) renders colour, mask and depth; `to_trimesh()` tessellates a CadQuery shape. Depth is along the view axis in normalised units. |
| `op_checker.py` | `OpTrace` wraps every `cq.Workplane` operation (even inside one chained statement) and asks OpenCascade after each step whether the result is legal. **error**: kernel exception, `BRepCheck_Analyzer` failure, or all material removed → `IllegalOperation` with step, line and a fix hint. **warning**: operation changed nothing, selector matched nothing, part split into pieces. One JSON record per step. |
| `generate_solid.py` | Runs a program (`result = ...`) under `OpTrace`, checks the solid, exports `solid.step` / `solid.stl`, renders the rig. `render_mesh()` is the shared render half (also used for GT targets). Writes `<view>.png`, `<view>_mask.png`, `<view>_depth.png`, `depth.npz`, `ops_log.jsonl`, `info.json` (normalisation, bbox, solids/faces/volume, op warnings). Exit 1 on illegal programs. Flags: `--like`, `--center-at`, `--rig`. |

### Data and starting programs

| File | Role |
|---|---|
| `data/fusion360_targets.py` | For each part in the split: map the GT to the cadrille frame (`to_target_frame`), render with `render_mesh`, write `data/generated/targets/fusion360/<part>/` with `gt.stl` (offline scoring only) and `info.json` (source, units, watertight flag, face/vertex counts). |
| `cadrille_init.py split` | Stratified 60-part subset: cadrille-RL IoU bin (low < 0.6, mid 0.6–0.9, high ≥ 0.9) × mesh complexity (faces + vertices vs. median 1512), 10 per cell, seed 2529. Writes `data/fusion360/stage1.txt` and `stage1_meta.json` (strata used by the summaries). |
| `cadrille_init.py tune` | **Tuning set** for pilots and prompt changes: 3 parts per IoU bin (9), same strata, drawn only from test parts outside Stage 1 (seed 2530) → `data/fusion360/tuning.txt` + `tuning_meta.json`. Build with `fusion360_targets.py --split data/fusion360/tuning.txt --out data/generated/targets/fusion360_tuning` and `convert --targets data/generated/targets/fusion360_tuning --out data/generated/init/cadrille_rl_tuning`. The first three pilots used 3 Stage 1 parts (127274_6484a80b_0000, 135654_34a24e52_0000, 22011_0832eefe_0013); report them as seen during development. |
| `cadrille_init.py convert` | Turns `cadrille/work_dirs/f360_<tag>_test/py/<part>.py` into a refine program (`to_refine_program`: adds `result = r`), builds it, then the **placement fit**: isotropic scale `s ∈ [0.7, 1.4]` by a 13-point log grid + golden-section search, maximising the weighted geo score against the target renders (GT-free). Applied only if `|s−1| > 0.005` and the score gains > 1e-3, as a visible code line `result = cq.Workplane(obj=result.val().scale(s))`. Logs to `init_log.json`. `--no-placement` ablates it. |

### The geometric checker (contribution 2)

| File | Role |
|---|---|
| `compare.py` | Per view: silhouette IoU, missing / extra pixels, depth MAE on the overlap (shown to the agent), and the score's depth term `depth_err`: over the union of both silhouettes, `min(|Δdepth|, DEPTH_CAP)` where both cover and `DEPTH_CAP` (0.1 normalised units) where only one does, so it is defined without overlap and an edit cannot lower it by shrinking the overlap. Writes overlay images (red = missing, blue = extra) and depth-error heatmaps to `<cand>/diff/`. `largest_residual()` finds the largest connected missing/extra blob for the zoomed detail tile. |
| `view_weights.py` | Confidence per **target** view. Each view's depth is back-projected to 3D and projected into every other view (space carving): a point must land on the other view's silhouette and must not be in front of its visible surface (`DEPTH_TOL = 0.03`, 3×3 min-filter on depth). `r(v,u)` = symmetric rejection rate; `c_v = 1 − median_u r(v,u)`; `w_v = clip((c_v − 0.6)/(0.98 − 0.6), 0, 1)`. The median means one bad view cannot drag good ones down. Clean renders give exactly 1.0; cached in `<target>/view_weights.json`. |
| `geo_check.py` | `geo_score` = weighted mean silhouette IoU − weighted mean `depth_err` (old reports: depth MAE). `geo_accept(cur, new, w)` keeps an edit iff the gain > `min_gain` (1e-3) **and** no *trusted* view (`w ≥ 0.5`) loses more than 0.05 IoU. `|gain| ≤ min_gain` is flagged *inconclusive*. `residual_table` is the per-view table shown to the agent (with the weight column). |

### The agent

`vlm.py` holds everything model-facing.

- **Backends.** `chat(messages, backend=...)` dispatches through `BACKENDS`:
  `vertex` (default; `vertex_ai.py`, Gemini via google-genai with ADC auth, project/model
  from `.env`, retries 429/5xx, thinking tokens counted as output), `ollama` (streams from `http://localhost:11434/api/chat`, returns token stats) and `echo`
  (deterministic fake: seeded by the text + image bytes; perturbs one number in the program by
  ×0.9/×1.1 with a `CHANGE: dimensional` line, sometimes `NO_CHANGE`; answers judge / question /
  answer / feedback prompts in the right format).
- **Code safety.** `extract_code` pulls the fenced block; `check_code` allows only `cadquery` and
  `math` imports, forbids `open/exec/eval/__import__/...`, and requires `result`.
- **System prompt** (`SYSTEM`): units, workplane frames, GATOR-style
  rules (current program is the scaffold, keep frame and scale, local targeted edits), and the
  reply format: first line `CHANGE: <structural|dimensional|positional> — <reason>` or exactly
  `NO_CHANGE`.
- **Prompts.** `initial_prompt` (from scratch), `refine_prompt` (current program; optional
  residual table, detail tile note, kernel report, QA feedback, gsolver table),
  `repair_prompt` (the build error, including op_checker's diagnosis), `kernel_report` (solid count, volume,
  per-operation warnings), `VLM_JUDGE` (A/B with randomised order → `KEEP A|B`).
- **CADCodeVerify-style questions.** `QUESTIONS_PROMPT` (2–5 yes/no questions from the target),
  `ANSWER_PROMPT` (Yes / No / Unclear + reasoning per question), `FEEDBACK_PROMPT` (turn
  No/Unclear into corrections), with parsers `parse_questions`, `parse_answers`, `qa_text`.

### The loop

`refine.py`. Per part:

1. **Setup.** Load the rig, measure the target bbox and centre from depth, compute view weights,
   render the target grid (`front right top iso_fr`, 2×2).
2. **Round 0** (`prepare_init`). Build the `--init` program into `<part>/init/`. If it fails,
   the part is skipped. Without `--init` the agent writes the first program.
3. **Questions** (`part_questions`, question arms only). Written once from the target and cached
   in `questions.json`. **Sanity filter:** they are also answered on the target itself, and only
   those answered "Yes" there are kept.
4. **Rounds** for each arm (`refine_part`):
   1. stop if `--budget-seconds` is used up;
   2. question arms: answer the questions on the current candidate; otherwise ask for feedback
      on the No/Unclear ones. All "Yes" → stop (`all_questions_yes`) in `vlm`/`gsolver`
      (CADCodeVerify). Arms that also see the geometric evidence (`hybrid`) stop only if the
      weighted silhouette IoU is ≥ `ALL_YES_IOU` (0.98) too; otherwise they continue without
      question feedback (`qa_all_yes_continued`);
   3. collect evidence: target grid + candidate grid, and for residual arms the overlay grid,
      depth-error grid, zoomed detail strip and the weighted residual table;
   4. `Agent.write_program`: send the prompt, check the code, build; on a build error send the
      error back (up to `--repairs`, default 2). `NO_CHANGE` → stop.
   5. score the new candidate (`score`: compare + geo score + offline `eval3d`);
   6. decide (table below). The geo decision is computed and logged for **every** arm (shadow);
      the judge runs where the rule needs it, or everywhere with `--shadow-judge`;
   7. log the row; if kept, it becomes the current state.
5. **Best checkpoints.** `best_geo` = best kept state by the GT-free geo score (what a deployed
   system would pick); `best_oracle` = best state ever built by hidden 3D IoU (analysis only).

| arm | extra evidence for the agent | edit kept if |
|---|---|---|
| `premise` | — (just target and candidate grids) | VLM judge prefers the new version |
| `vlm` | failed verification questions + feedback | VLM judge |
| `geo` (main method) | residual images, detail tile, weighted table | `geo_accept` |
| `hybrid` (ablation) | everything above | `geo_accept` **and** judge; judge alone if the geo gain is inconclusive |
| `oracle` | as `geo` | hidden 3D IoU rises (analysis only) |
| `gsolver` | as `vlm` + GT-vs-candidate properties (size, volume, area, pieces, through-holes, centroid) | always (CADCodeVerify's geometric-solver* upper bound; uses GT) |

All arms receive the kernel report (unless `--no-kernel`). `--arm main` = the first four,
`--arm all` = all six, or a comma list.

**Offline label per edit** (`verdict_of`): beneficial if 3D IoU rises by more than 0.005,
harmful if it falls by more than 0.005, else neutral.

**Sandbox (opt-in, Linux).** `sandbox.py` wraps the build subprocess in bubblewrap when
`--sandbox` is given (`refine.py`, `cadrille_init.py convert`): all namespaces unshared (no
network); `/usr`, `/etc`, `/sys` read-only; home hidden except the repo code, venv and uv's
Python install (read-only); `runs/`, `data/`, `cadrille/`, `archive/`, `.git` masked; only the
target's `info.json` visible; the candidate folder and a fresh `/tmp` writable; GPU device nodes
passed through for EGL. `vlm.check_code` alone is not enough: e.g. `cq.exporters.export(...)`
passes it and can write anywhere (`tests/test_sandbox.py` shows this). Renders are unchanged
(masks and depth identical, shading within 1 grey level).

**Flags.** `--rounds` (4), `--budget-seconds`, `--repairs` (2), `--backend`, `--model`, `--think`,
`--init`, `--shadow-judge`, `--sandbox`, `--seed`, `--name`, `--out`, and ablations `--no-weights`,
`--no-kernel`, `--no-residuals`, `--no-residual-images`, `--no-detail`, `--no-images`.

### Evaluation and reporting

| File | Role |
|---|---|
| `eval3d.py` | Offline only; the agent and acceptance rules never call it on their own decisions. With `gt.stl`: mesh-boolean volume IoU and IoGT via manifold3d (per connected piece); with `solid.step`: exact OCC booleans. Surface metrics on 30 000 samples: Chamfer ×1000, Hausdorff, F1 at 1% of the bbox diameter, normal consistency. **cadrille protocol** (each mesh unit-cube normalised, 8192 points): `iou3d_cad`, `cd_cad` = mean squared distance ×1000 — round 0 reproduces cadrille's published per-part scores. `failed()` = overlap 0, distances None. `properties()` feeds the gsolver arm. |
| `summarize_runs.py` | Per arm: median (IQR) and mean of `iou3d, iou3d_cad, cd_cad, chamfer_x1000, hausdorff, f1, iogt` at round 0 / final / best_geo / best_oracle; gains; invalid-proposal rate and repair success; acceptance rate; kept-precision, harmful-accept rate and good-recall for the real and shadow decisions; geo–VLM agreement; change-tag distribution; stop reasons; tokens and seconds; gains per stratum. Writes `results/summary.json`, `results/parts.csv`, `results/edits.csv`. |
| `figures.py` | `results/figures/`: `iou_by_round.png`, `iou_vs_time.png`, `edit_outcomes.png`. |
| `report.py` | After every part: `README.md` (status, headline table, where to look, terms), `results.md` (every part × arm, worst start first), `parts/<part>/compare.png` (target / start / each arm's final: 4 renders + 4 depth-error maps) and `scores.md` (round-by-round table). |
| `progress.py` | Called by `report.py`: `parts/<part>/progress.png` (per arm a strip start → round 1 → ..., shape over depth error in the view where the start was most wrong, framed green kept / red rejected, + a 3D IoU-by-round chart) and `results/figures/progress_by_part.png` (small multiples, one IoU-by-round chart per part, worst start first). |
| `layout.py` | Paths inside a rendered-solid folder (`renders/`, `diff/`, `internal/`); readers fall back to the old flat layout. |
| `compare_image.py` | Older single-image checker (camera search + outline IoU); not used by the Stage 1 loop. |

## 5. Output layout

```
runs/<date>_<name>/                    (--name; --out sets the folder exactly)
  README.md  results.md                start here / every part x arm
  results/                             summary.json  parts.csv  edits.csv  figures/
  config.json  log.txt                 all flags (+ target paths) / console output
  parts/<part>/
    progress.png                       start → round 1 → ... per arm (one view) + IoU chart
    compare.png  scores.md             final programs in 4 views / round-by-round table
    questions.json                     verification questions (question arms)
    internal/view_weights.json
    init/                              starting program (internal/init.json: source, error)
    <arm>/
      final -> round_XX_kept | ../init the state the arm ended with
      log.jsonl                        one row per round (see below)
      result.json                      stop reason, final + best_geo + best_oracle metrics, usage
      round_XX_<outcome>/              kept | rejected | failed | no-change | stopped
```

Every program folder (targets too, see `layout.py`): `program.py`, `solid.stl`/`solid.step`,
`conversation.json` (prompt, transcript, decision, QA), `renders/` (4 cameras: shaded, mask,
depth), `diff/` (overlay + depth-error images, `summary.png`, `report.json`), `internal/`
(`info.json`, `depth.npz`, `ops_log.jsonl`). Inputs (targets, starting programs) live in the
git-ignored `data/generated/`; runs from before this layout are in `archive/runs_until_2026-11-18/`.

A `log.jsonl` row for a built edit contains: `round, status, attempts, repairs_used,
change_tag, change, accepted, verdict, geo_decision, geo_gain, geo_inconclusive, vlm_decision,
mean_iou, w_iou, depth_mae, geo_score, kernel_warnings`, all `eval3d` metrics, `iou3d_before`,
`qa_yes/qa_n` (question arms), `detail_view`, token/time usage and `wall_seconds`.

## 6. Tests

`uv run pytest` (70 tests, `testpaths = ["tests"]`).

| Test file | Checks |
|---|---|
| `test_fusion360_pipeline.py` | GT rendered as a candidate is perfect; cadrille programs build; round-0 cadrille-protocol IoU matches `scores.json`; placement recovers a known scale. |
| `test_view_weights_and_geo_check.py` | Clean views weigh 1; a corrupted view is the only one down-weighted; low-weight views cannot veto; trusted views can. |
| `test_vlm_parsing.py` | `CHANGE:` / `NO_CHANGE`, questions, answers, `KEEP`, code checks, kernel report, repair prompt. |
| `test_sandbox.py` | Sandbox blocks other files, network and writes; a program that passes `check_code` but exports a file is contained; sandboxed renders match plain ones. Skipped off Linux. |
| `test_vertex_ai.py` | Vertex backend with a stubbed Gemini client: `.env` parsing (shell wins), config errors, message/image conversion, token stats incl. thinking, cut-off, thinking level, retry on 429 only, `vlm` defaults to vertex, `refine` errors on missing config. |
| `test_refine_echo.py` | Every arm end to end with the echo agent; shadow decisions and usage logged; round folders named by outcome, `final` link, README / results.md / compare.png written; a failing start program is skipped; default run folder is `runs/<date>_<name>`. |
| `test_compare.py`, `test_compare_image.py`, `test_illegal_shapes.py` | Checker scores/colours, image checker, op_checker catches illegal operations at the right step. |

`tests/conftest.py` provides a session fixture `f360_target` (part `101190_cfdcb477_0005`).

## 7. Known limits (accepted for the proof of concept)

- **Centring** forgives translation errors (`--center-at`); scoring is otherwise fixed-frame.
- **Placement** fits isotropic scale only — no rotation or per-axis scale.
- **cadrille's inputs** were its own 4-view renders (`cadrille/eval_fusion360.py`), not our 4 cameras.
- cadrille cannot be the editing agent: it is a fine-tuned image→code model, not instruction-following.
- Echo-backend numbers are meaningless; no real-model run has been done yet.
- Not yet built: Stage 2 (corrupted views). The Vertex backend has no real run yet.
