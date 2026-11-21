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

## 3. Results (checker study, 2026-11-20)

Run `runs/2026-11-20_stage2_checker/` (git-ignored; regenerate with the commands above).
The run covered 56 of the 60 Stage 1 parts. The other 4 have non-watertight GT meshes, so
there is no 3D IoU to label their edits. Each part had 8 edits plus the starting program,
which gives 2,804 non-neutral edits per condition.

| condition | right decisions | harmful kept | rank corr. | weights help? |
|---|---|---|---|---|
| clean | 93% | 4% | 0.89 | (all weights 1) |
| holes / blobs / depth_noise, L3 | 93% | 4% | 0.87–0.89 | no difference |
| bad_view L3 (one view shifted 32 px) | 92% on, 91% off | 4% | 0.88 | +1 pt |
| jitter L3 | 89% on, 88% off | 7% | 0.78 | +1 pt |
| depth_scale L3 (2% per view) | **87% on**, 93% off | **9% on**, 4% off | 0.75 / 0.86 | **hurts** |
| erode L3 (6 px) | 75% | 20% | 0.55 | no |
| dilate L3 (6 px) | **70%** | **23%** | 0.51 | no (weights stay 1.00) |

1. **On clean views the checker is a good judge.** It gets 93% of edit decisions right, keeps
   only 4% of harmful edits, and ranks programs much like the hidden 3D IoU (Spearman 0.89).
2. **Random, local damage barely matters.** That covers holes, blobs, smooth depth noise, and
   even one view shifted by 32 px. Both programs in an edit are compared with the *same* damaged
   pixels, so most of the damage cancels in the score *difference* that `geo_accept` uses. One
   bad view out of eight is diluted by the other seven even without weights.
3. **A systematic boundary bias breaks it.** A silhouette dilated by 6 px makes the checker keep
   23% of harmful edits instead of 4%, because a fattened target rewards programs that are too
   big. Erosion does the same in the other direction. The bias points one way, so it does not
   cancel. The view weights cannot see it either: a uniformly dilated set of views still agrees
   with itself, so every weight stays 1.00.
4. **View weights help a little on a bad view and hurt on depth-scale errors.** A per-view depth
   scale error drives some weights down to ~0.26. The weights then also discount those views'
   silhouettes, which were perfect, and accuracy drops from 93% to 87%. The weights mix two
   things that should be separate: whether a view's *depth* is trustworthy and whether its
   *silhouette* is.

**What this suggests for the noise-tolerant rule** (proposal, Week 4):
- **Split the weights.** Use a silhouette weight from mask-only consistency and a depth weight
  from depth consistency, and apply each to its own term in `geo_score`. That should remove the
  depth-scale regression and keep the bad-view gain.
- **Tolerate boundary bias.** Ignore a band of a few px around the target boundary in the IoU,
  or estimate a uniform boundary offset per view and remove it before scoring. This targets
  erode/dilate, the only corruptions that really hurt.
- Both can be tested offline with `checker_eval.py`: the candidates are cached, so a new rule
  only re-runs the 2D comparison. Tune on the tuning set, then report on the 60 parts.

**Caveats.** The edits are random one-number changes, not Gemini's edits. Gemini's edits are
more structured and may be subtler. The study tests the checker as a judge, not how noisy
residual images change what the agent proposes. Candidates are centred with the clean bbox
(section 2).

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
- **A noise-tolerant acceptance rule** (split weights, boundary-bias tolerance; section 3).
