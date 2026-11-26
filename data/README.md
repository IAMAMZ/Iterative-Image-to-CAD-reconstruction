# data/

Three datasets, each with a `dev` and a `test` split and the same layout:

```
data/<dataset>/<split>/
    ids.txt                       parts in the split
    images/<id>/rgb/<view>.png    the 4 input views (RealCAD: rgb/1.jpg .. 4.jpg, real photos)
    images/<id>/mask/<view>.png   synthetic: rendered; RealCAD test + test50: SAM 3 from the photo
    images/<id>/depth.npz         synthetic: rendered (float16 per view); RealCAD test50: VGGT from the photos
    poses/<id>.json               synthetic: centre, scale, R_table (object pose), table info; RealCAD test50: VGGT cameras
    meshes/<id>.stl (.step)       hidden ground truth; *_table_posed.stl = GT in the render frame
    manifest.json                 synthetic datasets only: render log for the split
```

| dataset   | dev | test | images | poses | meshes | notes |
|-----------|----:|-----:|--------|-------|--------|-------|
| deepcad   | 100 | 100  | 4 table views (rendered) | yes | stl + step (built from `deepcad/cad_json`) | |
| fusion360 | 572 | 345 | 4 table views (rendered) | yes | stl | dev = former "train", trimmed to the 572 parts cadrille RL was run on (other 808 in `archive/fusion360_dev_unrun`); all parts come from `raw/fusion360_test_mesh` |
| realcad   | 100 | 239 (+ test50: 50, test50_gt: same 50) | 4 real photos, downscaled to 1024 px (originals are 4032x3024) | test50 only, estimated from the photos (VGGT) | stl + step (built from `realcad/cad_json`) | test + test50 = 100 seeded picks + the 189 other built meshes; test50 = the first 50 of that list, which already have masks, cameras and depth (see below) |

The 4 views are the "table" cameras of `cameras.json` (`top_left`, `top_right`, `top_front`, `top_back`).
The old 6 axis views are in `archive/` (git-ignored).

Everything here is tracked in git except two folders of original downloads and the git-ignored `archive/` at the repo root:

| not in git | what it is | how to get it |
|---|---|---|
| `realcad/src/` (3.3 GB) | full-resolution RealCAD photos, `src/cad_real/<group>/<id>/{1..4}.jpg` (4032x3024) | ask Metom for a copy and unpack it to that path. Only needed to regenerate the downscaled inputs with `python make_realcad_images.py` |
| `raw/` | Fusion360 source meshes `raw/fusion360_test_mesh` (Hugging Face `maksimko123/fusion360_test_mesh`) and DeepCAD json archives | only needed to re-render / rebuild; the renders, poses and meshes below are already tracked |

The RealCAD photos in `realcad/<split>/images/` are the tracked, downscaled inputs (long side 1024 px, made by `make_realcad_images.py`); the originals are not in git.
The originals carry no EXIF (no focal length / phone model), so RealCAD camera intrinsics are unknown and must be estimated.

### RealCAD masks, cameras and depth (from the photos only)

Everything below is estimated from the 4 photos of a part; no CAD and no ground truth is used.
The capture rig is a fixed phone camera; the part is turned on the table (about 90 deg) between the 4 photos.

Masks (`realcad/test*/images/<id>/mask/{1..4}.png`, QA in `realcad/test*/mask_qa.csv`): SAM 3 with a text prompt
on Kaggle (`sam3_realcad_masks.ipynb`), imported by `import_realcad_masks.py`.
- `test50`: current notebook (input `out/realcad_test50_rgb.zip`). Through-holes stay background (only SAM pinholes
  < 0.005 % of the photo are filled; 6 parts have see-through holes) and no photo is empty (low-score retry).
  Against the first GT-fit silhouettes, mean view IoU 0.918 (the first notebook version, holes filled: 0.897).
- `test`: still the first notebook version: all holes filled, 15 photos with an empty mask (flag `none`).
  Re-run the current notebook before using its masks.
No dev masks yet.

Cameras + depth (`realcad/test50` only so far): `prep_realcad_recon_inputs.py` (part cut out by its mask, one shared
square crop per part) -> `recon_realcad.ipynb` on Kaggle (VGGT-1B; `recon_realcad_da3.ipynb` = Depth Anything 3,
compared but not used) -> `convert_realcad_vggt.py --split test50 --crops realcad/test50/vggt_crops.json` writes
`poses/<id>.json` (per view: OpenGL camera-to-world + K in 1024x768 photo pixels; `quality`) and
`images/<id>/depth.npz`, `depth_conf.npz` (z-depth per view, full photo size, object units, 0 = no depth; views
with an empty mask have no key). The object frame comes from the prediction: +Z = the axis the part was turned
about (table normal), origin and scale = unit bounding sphere of the fused point cloud. It is NOT the CAD frame.
`quality.flag` is a self-check from the photos: `ok` (27 parts: the views agree on one camera elevation, as the
fixed camera requires), `inconsistent_views` (18: some VGGT views are wrong; per-view depth is still usable),
`symmetric_or_single_view` (5: the part looks the same from every side or has one masked view, so +Z uses the
typical elevation of the `ok` parts, 43 deg).
To extend to `test`: run `prep_realcad_recon_inputs.py --split test --n 239`, the notebook, then
`convert_realcad_vggt.py --split test --zip <its output>`.

### RealCAD test50_gt: the same 50 parts with perfect cameras and depth (uses the GT)

`realcad/test50_gt` has the same photos and the same SAM 3 masks as `test50`; its cameras and depth come from the GT
CAD mesh instead of VGGT. So `test50` vs `test50_gt` measures what VGGT costs, with the masks taken as solved
(in every disagreement we checked, the hole-kept SAM masks follow the photo more closely than any CAD fit).
It uses the ground truth: an upper bound, never an image-only input.

`fit_realcad_pose.py --split test50 --n 50 --out ../out/pose_fit_v3` places the GT mesh in each photo: one camera
per part, the part turned on the table between views; 48 starts (24 rest poses x 2 turn directions) fitted to the SAM
masks with differentiable point-splat silhouettes; the final start is chosen by the EXACT mesh outline (the soft one
blurs small holes away, so a plate flipped end for end scored the same), then polished on the exact outline (the soft
outline is 0.5-5 % larger than the exact one, which made fits come out slightly small). A weak capture prior from the
well-fitted parts (elevation 48.3 +- 3 deg, focal 752 px +- 3 %, each turn 90 +- 12 deg in one direction) breaks ties:
symmetric parts (rings, cylinders) used to wander to any turn, and thin cylinders to elevations up to 85 deg.
The phone sometimes moved a little between photos, so each view may move the camera along its line of sight
(prior +- 5 %; `quality.capture.view_distance_%`).
`realcad_gt_inputs.py` (default fit run `../out/pose_fit_v3`) writes the split: `mask/` = the SAM masks,
`depth.npz` = z-depth of the posed GT mesh kept where the SAM mask and the CAD silhouette agree (0 elsewhere),
`poses/<id>.json` = per view OpenGL camera-to-world + K in 1024x768 photo pixels, in the synthetic frame
(CAD axes, `p = (p_cad - centre) * scale`, `R_table` = I, `table_up` = table normal), `quality.capture` = how far the
fit is from the usual capture; `gt_fit_qa.csv` = per view IoU of the CAD silhouette vs the SAM mask and the share of
the mask that has depth. Unlike `test50` (VGGT frame) this is the GT frame, so report raw and aligned scores.

Check: median view IoU CAD silhouette vs SAM 0.958 (5 of 200 views < 0.85); per-view camera distance change median
1 %, at most 11.6 % (00050635 view 4). 3 parts are `quality.flag = check`: 00106978 (min 0.71), 00088279 (0.76),
00026341 (0.85). In all three the CAD outline runs past the end of the print in every view: the CAD bar looks
longer than the print, or its ends are shaped differently, so no camera explains it.
Fixed by the per-view distance: 00050635 and 00081261 (one photo taken from closer or farther: 0.80 -> 0.96,
0.86 -> 0.98). Fixed by the exact-outline choice: 00015962 (the plate was flipped end for end, hole at the wrong
end; 0.83 -> 0.92 in its worst view; the see-through part of the hole is still slightly off).
`realcad/test50_gt95` (`realcad_gt_inputs.py --subset 0.95`): the 32 parts of `test50_gt` whose cameras explain the
SAM masks best (mean view IoU >= 0.95; every view >= 0.94, mean 0.965), same files and layout. Use it when the
cameras must be trusted; compare against the same 32 ids of `test50`.
Earlier fit runs (`../out/pose_fit`, `pose_fit_refit`, `pose_fit_holes`, `pose_fit_v2`: against the first hole-filled
SAM masks, without the prior, or with one fixed camera) are kept for reference only.

RealCAD GT check (`realcad/gt_check.json`, sheets from `realcad_gt_sheets.py`): 384 of 389 GT meshes match their prints.
`dev/00147363` has an extra thin rod (in the source cad_json) that the print lacks, so its scores are unreliable;
`test/00115681` is uncertain; `test/00147229` and `test/00446108` are not watertight (volume / IoU unreliable).

Check the layout: `python check_layout.py`.
Regenerate: `render_views.py <dev|test>` (DeepCAD), `render_fusion360.py split|render <dev|test>`; splits by `make_split.py`; shapes rebuilt by `cad_build.py`.
