# Stage 2: imperfect masks and depth

Stage 1 gives the geometric checker perfect target masks and depth. Stage 2 asks the
proposal's second question: **how does forward-rendering verification hold up when the 2D
measurements are wrong, and do the view weights stop bad measurements from misleading it?**

Two tools, both reusing the Stage 1 code unchanged:

| file | what it does |
|---|---|
| `corrupt.py` | Writes noisy copies of target folders: 8 corruption kinds x 3 levels, seeded. |
| `checker_eval.py` | Measures how often `geo_accept` makes the right keep/reject call on each noisy copy, with and without view weights. No VLM calls. |

The noisy targets are ordinary target folders, so `refine.py` also runs on them directly
(the full loop with the agent, see the end of this page).

## 1. What gets corrupted

A target's measurements are one depth map per view (`internal/depth.npz`; the silhouette is
`depth > 0`). `corrupt.py` changes only those, plus the `_mask.png` / `_depth.png` previews made from them.
The shaded RGB renders the agent looks at, `gt.stl`, the normalisation and the folder name all stay the same.
That matches the real setting, where the photo is true and masks / depth are *estimated* from it (SAM 3, VGGT).
The clean target's cached `view_weights.json` is deleted so the weights are recomputed from the noisy views.

| kind | per view | L1 | L2 | L3 | models |
|---|---|---|---|---|---|
| `erode` | boundary moves in by r px | 1 | 3 | 6 | a segmenter that under-segments |
| `dilate` | boundary moves out by r px | 1 | 3 | 6 | a segmenter that over-segments, halo |
| `jitter` | boundary moves by a smooth random field (amplitude) | 2 | 4 | 8 px | ragged mask edges |
| `holes` | n missing blobs inside the silhouette | 2 small | 4 medium | 6 large | missed regions (specular, dark) |
| `blobs` | n spurious blobs grown from the boundary | 2 small | 4 medium | 6 large | shadows, background leaking in |
| `depth_noise` | smooth random depth error, std | .005 | .01 | .02 | monocular depth noise |
| `depth_scale` | depth x (1 +- e) about the camera, sign per view | 0.5% | 1% | 2% | per-view scale error |
| `bad_view` | **one** view shifted by s px (mask + depth) | 8 | 16 | 32 | a mis-registered / wrong view |

Renders are 512 px; depth is in normalised units (the part fits a unit sphere ~3.5 units
from the camera). For scale: `DEPTH_TOL` in `view_weights.py` is 0.03, and 2% of 3.5 is 0.07.

Levels share their random draws (same blob positions, same field, same bad view), so going up
a level only makes the *same* corruption stronger and curves over levels are monotone.
`info.json["corruption"]` records the kind, level, parameters, seed, which views were hit,
and the measured error per view (mask IoU and depth MAE against the clean view).

```sh
uv run python corrupt.py data/generated/targets/fusion360 --split data/fusion360/stage1.txt
#   -> data/generated/targets/fusion360_noisy/<kind>_L<level>/<part>/   (24 conditions)
uv run python corrupt.py data/generated/targets/fusion360 --preview 116646_96f3ebb8_0000 --view front
#   -> data/generated/targets/fusion360_noisy/preview_<part>.png  (kinds x levels, one view)
```

## 2. The checker study

For each part, `checker_eval.py` takes the cadrille starting program and K random edits of it.
An edit changes one number: x0.75, x0.9, x0.95, x1.05, x1.1 or x1.3, or a shift if the number is 0.
It builds each program once against the clean target and scores it once against `gt.stl`.

Every ordered pair (A → B) is one proposed edit. Its true label comes from the hidden 3D IoU, with the same rule as `refine.verdict_of`:
- beneficial: IoU rises by more than 0.005
- harmful: IoU falls by more than 0.005
- neutral: anything in between; neutral edits are left out of the rates

For each condition, the same candidates are compared with that condition's target views.
`geo_accept` then decides each edit twice, once with the target's view weights and once without.
Only the cheap 2D comparison is redone per condition, so the full sweep takes minutes of CPU and makes no API calls.

```sh
uv run python checker_eval.py data/generated/targets/fusion360 \
    --init data/generated/init/cadrille_rl --split data/fusion360/stage1.txt --edits 8
#   -> runs/<date>_stage2_checker/README.md  (table + figures)
```

Reported per condition and weights on/off:

| metric | meaning |
|---|---|
| right decisions | kept a beneficial edit or rejected a harmful one |
| right (subtle) | the same, for edits that changed 3D IoU by only 0.005–0.02 (late-round corrections) |
| harmful kept | share of harmful edits kept (the failure that costs accuracy) |
| good kept | share of beneficial edits kept |
| kept that helped | precision of the keep decision |
| rank corr. | per-part Spearman between geo score and 3D IoU over the candidates |
| w(hit views) / w(other views) | mean view weight of corrupted / untouched views |

**What this isolates.** It tests the checker as a *judge*. It does not test how noisy
residual images change what the agent proposes; that needs the full loop (section 4).

**Simplification.** Candidates are centred with the *clean* target's measured bbox centre.
In the loop the centre comes from the noisy target. That centre is the same for both sides of
an edit, so it shifts both and barely changes the decision.

## 3. Results

See `runs/<date>_stage2_checker/README.md` for the run's table and figures. Findings are
summarised in the PR that added this page.

## 4. Full loop on noisy targets

Noisy targets keep their part names, so the Stage 1 starting programs apply as they are:

```sh
uv run python refine.py data/generated/targets/fusion360_noisy/bad_view_L2/* \
    --init data/generated/init/cadrille_rl --arm geo,vlm,hybrid --rounds 4 --name stage2_bad_view_L2
uv run python refine.py ... --no-weights --name stage2_bad_view_L2_noweights   # ablation
```

The `vlm` arm only sees the shaded RGB, so mask/depth noise cannot reach it. The `geo` and
`hybrid` arms see residuals computed from the noisy measurements. That contrast is the point
of Stage 2.

**Tuning discipline.** As in Stage 1, choose any new rule or threshold (e.g. a noise-tolerant
`geo_accept`) on the 9-part tuning set (`data/fusion360/tuning.txt`), then evaluate it once on
the 60 Stage 1 parts.

## 5. Not yet done

- **Estimated observations.** Masks / depth from SAM 3 and VGGT on the RealCAD photos, from
  Metom's `data/realcad/test50`. They need a loader that turns his poses and depth into a
  target folder.
- **A noise-tolerant acceptance rule** beyond view weights, for corruptions that hit every view
  (see the results).
