# Ablation plan

The ablation shows which parts of the pipeline produce the gain. Every configuration changes
**one thing** from the main method and runs on the **same 36 Fusion360 parts**, so each result
is a paired comparison against `main`.

This round is **synthetic data only** (Fusion360 renders with exact masks and depth). RealCAD
photo targets come later, once the grid is settled here.

The run is split between two people. They run in parallel and each owns half the configs:

- [`ABLATION_RUN_A.md`](ABLATION_RUN_A.md): `main` plus the checker and feedback configs.
- [`ABLATION_RUN_B.md`](ABLATION_RUN_B.md): the `main_s1` noise floor plus the model, view,
  gate and patience configs.

This file is the shared design. Both runbooks depend on §3 (setup) being done first.

## 1. The main method (`main`)

| piece | setting | flag |
|---|---|---|
| round 0 | cadrille-RL program (4 of its own 128 px corner renders) | `--init data/generated/init/cadrille_rl` |
| editing agent | Gemini on Vertex (`VERTEX_MODEL` in `.env`, `gemini-3.8-flash`), temperature 1.0 | `--backend vertex` (default) |
| arm | `geo`: the geometric checker gates every edit | `--arm geo` |
| checker signal | silhouette IoU + depth error, with view weights | defaults |
| views | all 4 rig views (`top_front top_right top_back top_left`) | `--views all` (default) |
| agent evidence | residual images (split view: silhouette residual + \|depth error\|), per-view table, zoom tile, kernel report | defaults |
| edit feedback | attempt log + round history + repeat guard + edit-effect image | `--feedback image` (default since 2026-11-24) |
| gate | on: edit kept if weighted score gain > 0.001 and no trusted view loses > 0.05 IoU | `--gate on` (default) |
| patience | off | `--patience 0` (default) |
| rounds | 6 | `--rounds 6` |
| sandbox | on where available (bubblewrap, Linux only; does not change scores). Off on macOS | `--sandbox` |

Note that `refine.py` defaults differ from `main` in three places: `--arm` defaults to four
arms, `--rounds` to 4, and with no `--init` Gemini writes round 0. Always pass all three.

```
uv run python refine.py <36 targets> --init data/generated/init/cadrille_rl \
    --arm geo --rounds 6 --sandbox --name abl_main
```

## 2. Configurations

Each config is `main` plus the flags shown. The **owner** column says which runbook it is in.

### Required (12 configs)

| id | flags added to `main` | what it measures | owner |
|---|---|---|---|
| `main` | none | our method | A |
| `main_s1` | `--seed 1` | **noise floor**: a second identical run (see below) | B |
| `gemini` | drop `--init` | the loop without cadrille's round 0 (Gemini writes it) | B |
| `hybrid` | `--arm hybrid` | geo + CADCodeVerify-style questions + VLM judge: does visual review on top of geo help? | A |
| `mask_only` | `--geo-signal mask` | silhouette only: no depth images, no depth in the score | A |
| `depth_only` | `--geo-signal depth` | depth error only: no overlay images, no IoU guard (caveat below) | A |
| `one_view` | `--views worst` | 1 view instead of 4 (the worst at round 0, fixed); weights forced off | B |
| `no_gate` | `--gate off` | checker as information only: every built edit is kept | B |
| `patience1` | `--patience 1` | a failed edit may be explored for 1 more round before rollback | B |
| `patience2` | `--patience 2` | ... for 2 more rounds | B |
| `no_feedback` | `--feedback none` | no attempt log, history or repeat guard (the pre-feedback loop) | A |
| `fb_text_only` | `--feedback text` | feedback without the edit-effect image | A |

### Secondary (5 configs, if budget remains)

| id | flags added to `main` | what it measures | owner |
|---|---|---|---|
| `no_weights` | `--no-weights` | plain mean over views instead of view-confidence weights | A |
| `no_resid_img` | `--no-residual-images` | per-view table only, no residual images | A |
| `no_detail` | `--no-detail` | no zoom tile on the largest residual | B |
| `no_kernel` | `--no-kernel` | no CAD-kernel report | B |
| `signed_resid` | `--residual-view signed` | one grid with the outline and the **signed** depth error instead of the split pair (agent evidence only; same gate) | B |

### Free (no model calls)

| id | source | what it measures |
|---|---|---|
| `cadrille` | round 0 of `main` | the cadrille-RL baseline we start from |
| `gemini0` | round 0 of `gemini` | Gemini zero-shot image → CAD |

### Notes per config

- **`main_s1`.** `--seed` is not sent to Gemini; it only seeds the local RNG. So this is simply
  a rerun of `main`. An ablation delta smaller than the `main` vs `main_s1` difference is not
  a finding.
- **Two machines, two references.** A runs on Linux and B on macOS. Renders (EGL vs macOS
  OpenGL) and CAD tessellation can differ slightly between them, which moves scores a little.
  So each config is compared with the reference **from its own machine**: A's configs vs
  `main`, B's configs vs `main_s1`. `main` vs `main_s1` then measures chance plus the machine
  difference together.
- **`depth_only`.** `depth_err` is computed over the union of the two silhouettes and charges
  `DEPTH_CAP` where only one shape covers a pixel, so it still carries outline information.
  This is deliberate, since depth MAE on the overlap alone can be lowered by shrinking the part.
  The write-up should say "depth maps, which implicitly carry the outline", not "pure depth".
- **`one_view`.** The view is the one with the lowest geo score of the round-0 program,
  chosen without GT, and written to `parts/<part>/internal/views.json`. View weights need ≥ 3
  views, so they are off. Read it against `no_weights` to separate "1 view" from "no weights".
  The bounding box comes from that view's depth only, so the prompt calls it a lower bound.
- **`no_gate`.** `geo_accept` still runs and is logged as `geo_decision`, so kept-precision and
  harmful-accept rate show what the gate would have blocked. Report both `final` (no checker
  decisions at all) and `best_geo` (checker used only as a selector at the end).
- **`patience1/2`.** Branches are judged against the last committed state (the anchor), and
  the final state is always the anchor. The agent is told when it is on a tentative branch.
  Every round counts against `--rounds 6`. Tuning pilot (9 parts, 6 rounds): mean 3D IoU
  0.902 off, 0.886 p1, 0.892 p2, dominated by one part (115533). Without that part it was
  0.919 off vs 0.932 p2. The 36-part run decides it.
- **`fb_text_only` / `no_feedback`.** Tuning pilot: mean 3D IoU 0.902 image, 0.891 text, 0.862
  none (9 parts, one run each). Text vs image is too close to call on 9 parts, so it is
  measured at scale here.
- **`hybrid`.** It costs more because of the questions and the judge. It has not been run with
  feedback on yet, so B should not wait on A's numbers to budget it.
- **`signed_resid`.** This is a new flag (PR #13) with no tuning pilot yet. Pilot it on the 9
  tuning parts first (§4) and run it only if the pilot looks sane.

Not in the grid (optional): `premise` and `vlm` arms (VLM judge only, no geometry), and
`gemini` × `hybrid` as a 2×2.

## 3. Shared setup (once, before either runbook)

Both people must score **identical inputs**. The steps below are done by A, who then sends B
the files. Data under `data/generated/` and `runs/` is git-ignored.

1. **Part list.** 36 parts: 6 per cell (3 cadrille-IoU bins × 2 complexity bins, every cell
   has 10), from the 60 Stage 1 parts, seed 2531. Write and commit
   `data/fusion360/ablation.txt`:

   ```
   uv run python - <<'EOF'
   import json, random
   m = json.load(open("data/fusion360/stage1_meta.json"))["parts"]
   rng = random.Random(2531)
   pick = []
   for b in ("low", "mid", "high"):
       for c in ("simple", "complex"):
           cell = sorted(p for p, v in m.items() if v["iou_bin"] == b and v["mesh"] == c)
           pick += sorted(rng.sample(cell, 6))
   open("data/fusion360/ablation.txt", "w").write("\n".join(pick) + "\n")
   EOF
   ```

2. **Targets and round-0 programs.** A sends B a tarball of the exact folders instead of B
   regenerating them:

   ```
   tar czf ablation_inputs.tgz data/generated/targets/fusion360 data/generated/init/cadrille_rl \
       data/generated/targets/fusion360_tuning data/generated/init/cadrille_rl_tuning
   ```

   The tuning folders are for B's `signed_resid` pilot.
3. **Same code and model.** Both are on the same `main` commit, run `uv sync`, and use the
   same `VERTEX_MODEL` and `VERTEX_PRICE_*_PER_M` in `.env`. Each person may use their own
   Vertex project, since rate limits are per project.

4. **Cross-check.** After B's first run has round 0, compare its round-0 `iou3d` and
   `geo_score` with A's `main` round 0 for the same parts (`log.jsonl`, the `round: 0` row).
   The round-0 program is the same file on both sides, so they should agree to within about
   0.01. Small differences are expected from the two platforms. A larger gap means a different
   input or library version: stop and find it before going on.

The 36 targets as shell arguments (bash), used by both runbooks:

```bash
mapfile -t T < <(sed 's|^|data/generated/targets/fusion360/|' data/fusion360/ablation.txt)
uv run python refine.py "${T[@]}" ...
```

## 4. Pilots (tuning parts only)

Pilots run only on the 9 tuning parts (`data/generated/targets/fusion360_tuning`, init
`data/generated/init/cadrille_rl_tuning`), never on the 36 ablation parts.

The tuning pilots already cover `main`, `no_feedback`, `fb_text_only`, `patience1` and
`patience2` (`runs/2026-11-24_*`). Still to pilot, each for 9 parts × 6 rounds:

- `hybrid` with feedback on (A), to measure its cost;
- `signed_resid` (B), to check it is sane before the 36-part run.

The other configs were checked with echo tests and change only things already exercised.
Pilot them only if a 36-part run looks broken.

## 5. Budget and time

The measured cost on the tuning pilots (geo, 6 rounds, feedback image) is about **$0.32–0.36
and 10 min per part**. Parts in one run go one after another, so a config of 36 parts is about
**$12–13 and 6 h**. Runs of different configs are independent and can run in parallel
(about 3 per person, within Vertex rate limits).

| | configs | estimate |
|---|---|---|
| A required | 6 (`hybrid` counted as ~2×) | ~$90, ~12–14 h at 3 in parallel |
| B required | 6 (`one_view` cheaper) | ~$70, ~12 h at 3 in parallel |
| secondary | 5 | ~$60 |
| total | 17 | ~$220 |

These numbers come from 9 tuning parts. Check the first finished 36-part run against them
before starting the rest.

## 6. Collecting results

- Each run is written to `runs/<date>_abl_<id>/` with its own README.md, results and
  `config.json`, which records every flag.
- When B is done, B sends A the `runs/*_abl_*` folders as a tarball. Folder names must keep the
  `abl_<id>` pattern.
- `refine.py` cannot resume a run that dies. The missing parts are rerun as
  `abl_<id>_part2`, and the summary treats `abl_<id>` + `abl_<id>_part2` as one config.
- **Summary (not built yet): `summarize_ablation.py`.** It reads every `runs/*_abl_*` folder
  and writes `runs/ablation_summary/` (README.md + CSV + figures), with:
  - one row per config: median/mean 3D IoU (`iou3d`, `iou3d_cad`), CD, gain over round 0,
    `final` and `best_geo`, kept-precision, harmful-accept rate, invalid-edit rate, tokens, $,
    minutes;
  - the **paired difference vs the same machine's reference** per part (A's configs vs
    `main`, B's vs `main_s1`): mean Δ IoU with a bootstrap 95% CI (10 000
    resamples over parts), a Wilcoxon signed-rank p-value, and wins/ties/losses;
  - the `main` vs `main_s1` difference as the noise floor in the same table;
  - Δ per stratum (low/mid/high start IoU);
  - figures: a forest plot of Δ IoU vs `main` with CIs, and IoU by round for each config.
- Until it exists, `summarize_runs.py` gives per-run numbers.

## 7. What is built

| piece | status |
|---|---|
| `--geo-signal`, `--views`, `--gate` | built (2026-11-24), echo tests |
| `--feedback none/text/image` (default image) | built (2026-11-24), tuning pilot done |
| `--patience K` (`refine.Branch`) | built (2026-11-24), `tests/test_patience.py`, tuning pilot done |
| `--residual-view signed` | built (PR #13), needs a tuning pilot |
| `--no-weights`, `--no-residual-images`, `--no-detail`, `--no-kernel` | built |
| `data/fusion360/ablation.txt` | written (2026-11-26): 36 parts, 6 per cell, mean cadrille-RL IoU 0.704 |
| `ablation.py` runner | dropped: the runbooks use plain `refine.py` commands |
| `summarize_ablation.py` | not built (§6) |
