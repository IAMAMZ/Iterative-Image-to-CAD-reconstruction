# Iterative Image-to-CAD Reconstruction

Write a 3D part as code, then take pictures of it from fixed angles.

## Scripts

- `examples/flange.py` — a 3D part written as CadQuery code (just the shape, nothing else).
- `generate_solid.py` — runs a part file, checks the part is OK, saves it, and takes its pictures.
- `op_checker.py` — watches every CadQuery command as it runs and logs the illegal ones (with the line and a hint how to fix it).
- `cq_render.py` — the camera: turns a 3D shape into pictures.
- `rig.py` — decides where the 8 cameras stand; saves them in `rig.json`.
- `compare.py` — scores a guess against the real 3D part: how well outlines overlap (IoU) and how far off the depth is, per camera.
- `compare_image.py` — scores a guess against just a picture of the part (no 3D model): finds the camera angle, then compares outlines.

## Setup

```sh
uv sync                     # or: conda env create -f environment.yml
```

## Run

```sh
uv run python generate_solid.py examples/flange.py
```

Pictures and files appear in `out/flange/`.

Every command is checked by the CAD kernel and written to `out/flange/ops_log.jsonl`.
If a command is illegal the run stops, exits with code 1, and prints e.g.

```
[ERROR  ] step  6 (line 3) fillet(20): StdFail_NotDone: BRep_API: command not done
          hint: the fillet/chamfer is too big for the selected edges ...
```

## Test

```sh
uv run pytest tests -v -s
```

- `tests/test_illegal_shapes.py` — sends illegal commands and checks each is caught, at the right step, with a hint.
- `tests/test_fusion360_pipeline.py` — Fusion360 targets, cadrille programs, placement, 3D scores.
- `tests/test_view_weights_and_geo_check.py` — corrupted views get down-weighted; the weighted acceptance rule.
- `tests/test_vlm_parsing.py` — parsing of agent replies, question/answer prompts, program formatting.
- `tests/test_sandbox.py` — the sandbox blocks files, network and writes; builds are unchanged (Linux only).
- `tests/test_refine_echo.py` — the whole refinement loop, every arm, with a fake agent (no model).
- `tests/test_compare.py` — checks the scores and colours of the checker are right.
- `tests/test_compare_image.py` — checks the picture checker finds the right angle and scores wrong parts lower.

## Make your own part

Copy `examples/flange.py`, change the shape, and keep the last line as `result = ...`.

## Compare a guess to the real part

```sh
uv run python generate_solid.py real.py  --out out/real
uv run python generate_solid.py guess.py --out out/guess --like out/real   # same size frame!
uv run python compare.py out/real out/guess
```

Look at `out/guess/compare/summary.png`: red = material the guess is missing,
blue = extra material, the heatmap = how wrong the depth is (pale = right, dark = wrong).

## Compare a guess to just a picture

At test time there is no 3D model, only an image. This finds the camera angle
that best fits, lines the outlines up, and scores how well they match.

```sh
uv run python generate_solid.py guess.py --out out/guess
uv run python compare_image.py photo.png out/guess                  # camera unknown: search
uv run python compare_image.py photo.png out/guess --camera iso_fr  # camera known
```

Look at `out/guess/compare_image/summary.png`: the picture, the guess from the found
angle, and the overlay (red = missing, blue = extra). Size can't be judged from one
picture, so only the shape counts.

## Refinement loop (Stage 1)

Data: 345 Fusion360 test parts. Their ground-truth meshes and cadrille's predicted CadQuery
programs are committed (`cadrille/results/fusion360_test_gt/`, `cadrille/work_dirs/f360_rl/`; the SFT outputs are archived).
Stage 1 uses a stratified subset of 60 parts (cadrille-IoU bin x mesh complexity).

```sh
uv run python cadrille_init.py split                # -> data/fusion360/stage1.txt (+ stage1_meta.json)
uv run python data/fusion360_targets.py             # -> out/targets/fusion360/<part>/  (renders, depth, gt.stl)
uv run python cadrille_init.py convert --tag rl     # -> out/init/cadrille_rl/<part>.py (+ placement fit)
uv run python refine.py out/targets/fusion360/* --init out/init/cadrille_rl \
    --arm main --rounds 4 --backend ollama --out out/refine
uv run python summarize_runs.py out/refine          # tables, summary.json, per_part.csv, edits.csv
uv run python figures.py out/refine                 # out/refine/figures/
```

Dry run without any model: `--backend echo` (a fake agent that perturbs one number per round).

**Sandbox (Linux, opt-in).** `--sandbox` (on `refine.py` and `cadrille_init.py convert`) builds
every model-written program inside bubblewrap (`bwrap`): no network, home directory and data
hidden, only the candidate's output folder writable. Off by default so macOS/Windows work as before.

**Frame.** cadrille writes programs in a canonical frame with the longest side about 200; the
ground truth is mapped into the same frame, so lengths are "units", not mm.

**Round 0** is cadrille's program. Its scale is first fitted to the target's silhouettes and depth
maps (`cadrille_init.py`, a GATOR-style placement step, GT-free; `--no-placement` to ablate).

**Arms** (`--arm main` = premise,vlm,geo,hybrid; `--arm all` adds the two analysis arms). Every
arm also gets the **CAD-kernel report** (per-operation warnings such as no-op cuts or a part that
fell apart, from `op_checker.py`), and build errors go back to the agent for repair.

| arm | agent sees | edit kept if |
|---|---|---|
| `premise` | target + candidate renders | VLM judge (`KEEP A/B`) |
| `vlm` | + failed verification questions (CADCodeVerify-style) | VLM judge |
| `geo` | + silhouette/depth residuals, zoom on largest residual, per-view table with view weights | weighted forward-rendering check |
| `hybrid` | everything above | check passes **and** judge agrees (judge alone if the check is inconclusive) |
| `oracle` | as geo | hidden 3D IoU rises (upper bound, analysis only) |
| `gsolver` | as vlm + GT property table | always (CADCodeVerify's geometric-solver* upper bound) |

**View weights** (`view_weights.py`): each target view's depth is back-projected and checked
against all other views (space carving); views that disagree with the rest get a low weight, count
less in the score and cannot veto an edit. Clean renders give weight 1 for every view.

**Stopping:** `--rounds`, `--budget-seconds`, the agent replying `NO_CHANGE`, or every
verification question answered "Yes".

**Ablations:** `--no-weights`, `--no-kernel`, `--no-residuals`, `--no-residual-images`,
`--no-detail`, `--no-images`, `--no-placement` (cadrille_init), `--init` omitted (agent starts from
scratch), `--shadow-judge` (judge every edit in every arm for agreement statistics).

Files:
- `refine.py` — the loop, arms and logging (every edit logs the geometric check's decision, the
  judge's where it ran, and what it really did to the hidden shape).
- `sandbox.py` — optional bwrap sandbox for builds (`--sandbox`).
- `geo_check.py` — weighted score and acceptance rule. `view_weights.py` — view confidence.
- `vlm.py` — backends (`ollama`, `echo`), prompts, verification questions, reply parsing.
- `cadrille_init.py` — stratified split, cadrille programs -> starting programs, placement fit.
- `data/fusion360_targets.py` — targets from the GT meshes.
- `eval3d.py` — offline scores: 3D IoU, IoGT, Chamfer, Hausdorff, F1@1%, normal consistency, and
  cadrille-protocol IoU/CD (round 0 reproduces `cadrille/results/fusion360_test.md`).
- `summarize_runs.py`, `figures.py` — tables and plots.
- `archive/procedural/` — the old random-part generator used to test the renderer.
