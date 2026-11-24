# Ablation plan

The ablation shows which parts of the pipeline produce the gain. Every configuration changes
**one thing** from the main method and runs on the **same parts**, so each result is a paired
comparison against the main method.

**Main method (reference config `main`):** cadrille-RL program as round 0, Gemini (Vertex,
`VERTEX_MODEL`) as the editing agent, `geo` arm. The full geometric checker is on: silhouette IoU
plus depth error, view weights, residual images, detail tile and kernel report. All 4 rig views
(`top_front top_right top_back top_left`) are used. `geo_accept` decides every edit.

## 1. Configurations

### A. Where the program comes from (model axis)

| id | init | refine | what it measures | new code |
|---|---|---|---|---|
| `cadrille` | cadrille-RL | none (round 0 only) | the baseline we start from | none: round 0 of `main` |
| `gemini0` | Gemini from scratch | none (round 0 only) | Gemini zero-shot image → CAD | none: round 0 of `gemini` |
| `gemini` | Gemini from scratch | Gemini, `geo` | the loop without cadrille's starting program | none (omit `--init`) |
| `main` | cadrille-RL | Gemini, `geo` | **cadrille + Gemini** (our method) | none |

`cadrille` and `gemini0` add no model cost. They are read from round 0 of `main` and `gemini`.

### B. Checker vs checker + visual review

| id | change | question |
|---|---|---|
| `hybrid` | `--arm hybrid` (geo + CADCodeVerify-style questions + VLM judge) | does VLM visual review on top of geo help? |

Optional, if budget allows: `premise` and `vlm` (VLM judge only, no geometry) show how much
the geometric checker adds on its own.

### C. Parts of the geometric checker

Each signal is removed from **both** places it is used: the evidence the agent sees and the
score that decides whether an edit is kept.

| id | flag | agent sees | edit kept if |
|---|---|---|---|
| `mask_only` | `--geo-signal mask` *(new)* | overlay images (missing/extra); table with IoU, missing px, extra px | weighted IoU gain > `min_gain`, per-view IoU guard |
| `depth_only` | `--geo-signal depth` *(new)* | depth-error heatmaps; table with depth error only | weighted `depth_err` falls by > `min_gain`, no IoU guard |
| `no_weights` | `--no-weights` | as main, weight column = 1 | plain mean over views |
| `no_resid_img` | `--no-residual-images` | table only, no overlay/heatmap images | as main |
| `no_detail` | `--no-detail` | no zoomed detail tile | as main |
| `no_kernel` | `--no-kernel` | no OpenCascade/op_checker report | as main |

`mask_only` and `depth_only` are the required ones. The other four already exist as flags and
are secondary.

**Caveat for `depth_only`.** `depth_err` is computed over the union of the two silhouettes and
charges `DEPTH_CAP` wherever only one shape covers a pixel. It therefore already contains
silhouette information. This is deliberate: depth MAE on the overlap alone can be lowered by
shrinking the part. The write-up should state that `depth_only` means "depth maps, which
implicitly carry the outline", not "pure depth".

### D. One view instead of four

| id | flag | change |
|---|---|---|
| `one_view` | `--views worst` *(new)* | only the single worst view is used, for the agent's images and table and for the checker |

- **Which view.** The view with the lowest geo score of the **round-0** candidate against the
  target. This needs no GT and is the same view `progress.py` already highlights. It is fixed
  for the whole run, so that `cur` and `new` are always compared on the same view.
  (A per-round re-pick is a possible variant, but it makes the score non-stationary.)
- **Target image.** The target grid shows the same single view (a 1×1 tile at the grid's size).
- **View weights** need at least 3 views to cross-check, so they are off (weight 1). This config
  is therefore "1 view, no weights" compared with "4 views, weights". Read it against
  `no_weights` to separate the two effects.
- **Questions/judge** are not involved (geo arm).

### E. Firewall off (checker informs, does not gate)

| id | flag | change |
|---|---|---|
| `no_gate` | `--gate off` *(new)* | geo evidence is shown as in main; **every built edit is kept** |

- `geo_accept` still runs and is logged as the shadow decision. Kept-precision and
  harmful-accept rate then show directly what the firewall would have blocked.
- **Report both `final` and `best_geo`.** `best_geo` (best kept state by geo score) is itself a
  GT-free selection. `no_gate` + `best_geo` is "checker as a selector at the end". `no_gate` +
  `final` is "no checker decisions at all". This split is part of the result.

### F. Tree search: let bad edits run for a few rounds

| id | flag | change |
|---|---|---|
| `patience1` | `--patience 1` *(new)* | a rejected edit may be explored for 1 more round |
| `patience2` | `--patience 2` *(new)* | ... for 2 more rounds |

The search is depth-limited backtracking. It follows a single path and keeps an **anchor**
`A`, the last committed state.

```
A = H = round 0;  steps = 0
each round: agent edits H  ->  new  (build failure: nothing changes)
  if geo_accept(A, new):          commit    A = H = new, steps = 0
  elif steps < patience:          tentative H = new, steps += 1
  else:                           roll back H = A,   steps = 0   (new is discarded)
end of run: final = A (never an uncommitted branch)
```

- A tentative branch is always compared with the **anchor**, not with its parent. A sequence
  of bad steps therefore cannot drift: the branch has to beat the last good state to be
  committed.
- **Tell the agent** when it is on a tentative branch. Proposed prompt line: "Your last edit
  lowered the geometric score. It is kept tentatively for N more round(s): continue in this
  direction only if you believe it leads to a better shape; otherwise revert it." Without
  this line, the residuals simply tell the agent to undo the edit. Decide this in the pilot
  (see §5).
- New round outcomes: `tentative`, `committed`, `rolled-back`. These need a colour in
  `progress.py`/`figures.py`, and a stop/outcome entry in `summarize_runs.py`.
- Every round counts against `--rounds`, including exploratory ones, so the cost per part stays
  comparable.
- Stretch goal, not in the main grid: a real beam (B children per node, keep the best by geo
  score) multiplies cost by B.

### G. Noise floor

| id | change | why |
|---|---|---|
| `main_s1` | `main` with `--seed 1` | Gemini runs at temperature 1.0. A second `main` run measures how much two identical configs differ by chance. An ablation delta smaller than this is not a finding. |

## 2. Run size and budget

**Parts.** 36 parts, the same for every config: 6 per stratum cell (3 cadrille-IoU bins × 2
complexity bins), drawn from the 60 Stage 1 parts with a fixed seed and written to
`data/fusion360/ablation.txt`. This gives the "30–40 per configuration" and keeps the strata
balanced. All parts in a config use one seed (`--seed 0`). Only `main_s1` differs, and only
in the seed.

**Rounds.** The same `--rounds R` for every config. The patience configs need room to explore,
so the proposal is **R = 6** everywhere, including `main` (decide in the pilot; R = 4 leaves
`patience2` almost no rounds to commit).

**Config count.**

| group | configs that call the model |
|---|---|
| required | `main`, `gemini`, `hybrid`, `mask_only`, `depth_only`, `one_view`, `no_gate`, `patience1`, `patience2`, `main_s1` → **10** |
| secondary | `no_weights`, `no_resid_img`, `no_detail`, `no_kernel` → 4 |
| free | `cadrille`, `gemini0` (round 0 of existing runs) |

That is 10 × 36 = 360 part-runs required, plus 144 secondary.

**Cost and time (rough).** The only real run so far (`runs/2026-11-23_vertex_smoke`: 1 part,
1 round, gemini-3.8-flash) used about 12k tokens, cost $0.026 and took 0.7 min. Scaled linearly
to 6 rounds, that is about $0.15 and 4 min per part-run, so **about $55 and 24 h serial** for
the required set (hybrid costs more because of the questions and judge). These numbers come
from one round of one part. Measure them again in the pilot before the full run. Runs are
independent per config, so 3–4 configs can run in parallel within the Vertex rate limits.

## 3. Implementation

1. **`refine.py` flags** (all default to current behaviour):
   - `--geo-signal {both,mask,depth}`: passed to `geo_score`/`geo_accept` (a `signal`
     parameter in `geo_check.py`) and to the evidence block (which diff grids are sent, which
     table columns `residual_table` prints).
   - `--views {all,worst}`: chooses the view at round 0 and restricts `GRID_VIEWS`, the
     compare report used for scoring, `detail_strip`, the target grid and the table to that
     view. Forces weights off.
   - `--gate {on,off}`: `off` sets `keep = True` for the geo/hybrid rules; the geo decision is
     still logged.
   - `--patience K`: the anchor/branch logic above, a prompt line in `vlm.refine_prompt`, and
     new outcome labels.
   - `config.json` records all four, so `summarize_runs.py` can label runs.
2. **Part list:** `cadrille_init.py ablation`, which writes `data/fusion360/ablation.txt` and
   `ablation_meta.json` (6 per cell from `stage1_meta.json`, seed 2531).
3. **Runner:** `ablation.py` holds a table `config id → refine.py flags` (§1) and runs each
   config to `runs/<date>_abl_<id>/`. `--only id,id` runs a subset. A config that has already
   finished is skipped, so the runner can be restarted.
4. **Summary:** `summarize_ablation.py` reads every `runs/*_abl_*`. Its output:
   - one row per config: median/mean 3D IoU (`iou3d`, `iou3d_cad`), CD, gain over round 0,
     `final` and `best_geo`, kept-precision, harmful-accept rate, invalid-edit rate, tokens, $,
     minutes;
   - **paired difference vs `main`** per part: mean Δ IoU with a bootstrap 95% CI
     (10 000 resamples over parts), a Wilcoxon signed-rank p-value, and wins/ties/losses;
   - the `main` vs `main_s1` difference as the noise floor in the same table;
   - Δ per stratum (low/mid/high start IoU);
   - figures: a forest plot of Δ IoU vs `main` with CIs, and IoU-by-round for each config.
   - Output goes to `runs/ablation_summary/` (README.md + CSV + figures).
5. **Tests** (echo backend, in `tests/test_refine_echo.py`): one end-to-end test per new flag.
   `--gate off` keeps every built edit. `--views worst` scores one view. The `--patience`
   state machine commits, holds tentative edits, and rolls back, so `final` is never an
   uncommitted branch. `--geo-signal` changes the score and the evidence. Unit tests for the
   `geo_check` signal variants.

## 4. Order of work

1. Implement flags + tests (echo backend only).
2. **Pilot on the 9 tuning parts** (never on Stage 1 parts): every new config with
   `--rounds 6`. Check that the runs are sane, then measure real cost and time. Settle the
   open decisions in §5. Wait for go-ahead after the pilot report.
3. Freeze prompts and flags. Write `ablation.txt`.
4. Run the required configs, then the secondary ones if budget remains.
5. `summarize_ablation.py` → results table and forest plot for the report.

## 5. Open decisions (settle in the pilot)

- `--rounds`: 6 for all configs (proposed) or 4.
- Patience: whether to tell the agent it is on a tentative branch (proposed: yes).
- `one_view`: worst view fixed at round 0 (proposed) or re-picked each round.
- `gemini` (from scratch): also run it with `hybrid`? This is only needed if the write-up wants
  model × checker as a 2×2.
- Whether the main write-up includes the optional `premise`/`vlm` arms.
