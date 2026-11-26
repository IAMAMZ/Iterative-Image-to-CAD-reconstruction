# Ablation runbook B

Half of the ablation in [`ABLATION_PLAN.md`](ABLATION_PLAN.md): the `main_s1` noise floor plus
the model, view, gate and patience configs. Runbook A runs the other half (including `main`)
in parallel.

## 0. Before starting

1. Pull `main` (it must include `data/fusion360/ablation.txt` from A) and run `uv sync`.
2. Unpack A's inputs at the repo root, so you score exactly the same targets and round-0
   programs:

   ```
   tar xzf ablation_inputs.tgz
   ```

3. In `.env`, set the same `VERTEX_MODEL` (`gemini-3.8-flash`) and `VERTEX_PRICE_*_PER_M` as A.
   Your own Vertex project is fine.
4. Check that bubblewrap works (`--sandbox`). If it can't run, tell A. It does not change
   scores, but both sides should match.
5. Pilot `signed_resid` on the tuning parts (about 1.5 h). Run the full config in §2 only if
   this run looks sane: it builds, the images look right, and the score does not collapse
   compared with `runs/2026-11-24_fb_image` (mean 3D IoU 0.902):

   ```
   uv run python refine.py data/generated/targets/fusion360_tuning/* \
       --init data/generated/init/cadrille_rl_tuning --arm geo --rounds 6 --sandbox \
       --residual-view signed --name pilot_signed_resid
   ```

## 1. Required configs

Run these in **bash** from the repo root (type `bash` first if your shell is fish or zsh).
Each line is one config of 36 parts (about 6 h). Run about 3 at a time, each in its own
terminal, or add `nohup … > abl_<id>.log 2>&1 &`.

```bash
mapfile -t T < <(sed 's|^|data/generated/targets/fusion360/|' data/fusion360/ablation.txt)
I="--init data/generated/init/cadrille_rl --rounds 6 --sandbox"

uv run python refine.py "${T[@]}" $I --arm geo --seed 1                --name abl_main_s1
uv run python refine.py "${T[@]}" --rounds 6 --sandbox --arm geo       --name abl_gemini
uv run python refine.py "${T[@]}" $I --arm geo --views worst           --name abl_one_view
uv run python refine.py "${T[@]}" $I --arm geo --gate off              --name abl_no_gate
uv run python refine.py "${T[@]}" $I --arm geo --patience 1            --name abl_patience1
uv run python refine.py "${T[@]}" $I --arm geo --patience 2            --name abl_patience2
```

`abl_gemini` has **no `--init` on purpose**: Gemini writes round 0 itself.

Start `abl_main_s1` first. Once a few of its parts have round 0, do the **cross-check**
(plan §3 step 4): its round-0 `iou3d` must equal A's `abl_main` round 0 for the same parts. If
it doesn't, stop and sort out the difference with A before running anything else.

## 2. Secondary configs (if budget remains)

```bash
uv run python refine.py "${T[@]}" $I --arm geo --no-detail             --name abl_no_detail
uv run python refine.py "${T[@]}" $I --arm geo --no-kernel             --name abl_no_kernel
uv run python refine.py "${T[@]}" $I --arm geo --residual-view signed  --name abl_signed_resid
```

## 3. Checks while running

- `runs/<date>_abl_<id>/README.md` updates as parts finish. Look at the first few parts of
  each run for build failures or a part stuck on errors.
- After the first config finishes, compare its $ and min per part with plan §5.
- **If a run dies**, `refine.py` cannot resume it. Rerun only the parts that are missing from
  `runs/<date>_abl_<id>/parts/` (or have no `result.json`), with
  `--name abl_<id>_part2`. The summary merges `abl_<id>` and `abl_<id>_part2`.

## 4. Done

You are done when every part in these folders has finished:

| config | folder |
|---|---|
| `main_s1` | `runs/<date>_abl_main_s1` |
| `gemini` | `runs/<date>_abl_gemini` |
| `one_view` | `runs/<date>_abl_one_view` |
| `no_gate` | `runs/<date>_abl_no_gate` |
| `patience1` | `runs/<date>_abl_patience1` |
| `patience2` | `runs/<date>_abl_patience2` |
| (secondary) `no_detail`, `no_kernel`, `signed_resid` | `runs/<date>_abl_no_detail`, `runs/<date>_abl_no_kernel`, `runs/<date>_abl_signed_resid` |

Then send them to A (folder names unchanged), also counting any `_part2` folders:

```
tar czf ablation_B_runs.tgz runs/*_abl_*
```
