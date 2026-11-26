# Ablation runbook A

Half of the ablation in [`ABLATION_PLAN.md`](ABLATION_PLAN.md): `main` plus the checker and
feedback configs. Runbook B runs the other half in parallel.

A also does the shared setup (plan §3) and collects the results (plan §6).

## 0. Before starting

1. Do plan §3 step 1: write `data/fusion360/ablation.txt`, commit it and push it.
2. Send B `ablation_inputs.tgz` (plan §3 step 2).
3. Pilot `hybrid` on the tuning parts to measure its cost (about 1.5 h):

   ```
   uv run python refine.py data/generated/targets/fusion360_tuning/* \
       --init data/generated/init/cadrille_rl_tuning --arm hybrid --rounds 6 --sandbox \
       --name pilot_hybrid_fb
   ```

## 1. Required configs

Run these in **bash** from the repo root (type `bash` first if your shell is fish or zsh).
Each line is one config of 36 parts (about 6 h, longer for `hybrid`). Run about 3 at a time,
each in its own terminal, or add `nohup … > abl_<id>.log 2>&1 &`.

```bash
mapfile -t T < <(sed 's|^|data/generated/targets/fusion360/|' data/fusion360/ablation.txt)
I="--init data/generated/init/cadrille_rl --rounds 6 --sandbox"

uv run python refine.py "${T[@]}" $I --arm geo                         --name abl_main
uv run python refine.py "${T[@]}" $I --arm hybrid                      --name abl_hybrid
uv run python refine.py "${T[@]}" $I --arm geo --geo-signal mask       --name abl_mask_only
uv run python refine.py "${T[@]}" $I --arm geo --geo-signal depth      --name abl_depth_only
uv run python refine.py "${T[@]}" $I --arm geo --feedback none         --name abl_no_feedback
uv run python refine.py "${T[@]}" $I --arm geo --feedback text         --name abl_fb_text_only
```

Start `abl_main` first. B's cross-check (plan §3 step 4) compares against its round 0.

## 2. Secondary configs (if budget remains)

```bash
uv run python refine.py "${T[@]}" $I --arm geo --no-weights            --name abl_no_weights
uv run python refine.py "${T[@]}" $I --arm geo --no-residual-images    --name abl_no_resid_img
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
| `main` | `runs/<date>_abl_main` |
| `hybrid` | `runs/<date>_abl_hybrid` |
| `mask_only` | `runs/<date>_abl_mask_only` |
| `depth_only` | `runs/<date>_abl_depth_only` |
| `no_feedback` | `runs/<date>_abl_no_feedback` |
| `fb_text_only` | `runs/<date>_abl_fb_text_only` |
| (secondary) `no_weights`, `no_resid_img` | `runs/<date>_abl_no_weights`, `runs/<date>_abl_no_resid_img` |

Then collect B's folders and summarise (plan §6).
