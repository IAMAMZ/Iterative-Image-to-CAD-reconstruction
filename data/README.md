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
| realcad   | 100 | 239 (+ test50: 50) | 4 real photos, downscaled to 1024 px (originals are 4032x3024) | test50 only, estimated from the photos (VGGT) | stl + step (built from `realcad/cad_json`) | test + test50 = 100 seeded picks + the 189 other built meshes; test50 = the first 50 of that list, which already have masks, cameras and depth (see below) |

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

Masks (`realcad/test*/images/<id>/mask/{1..4}.png`, QA in `realcad/test*/mask_qa.csv`): SAM 3 with a text prompt,
run on Kaggle with the first version of `sam3_realcad_masks.ipynb`, imported by `import_realcad_masks.py`.
Known limits, accepted as is: 20 photos have an empty mask (flag `none`; 15 in test, 5 in test50), and all holes
were filled, so through-holes (washers, rings, frames) count as part. The current notebook fixes both if needed.
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

RealCAD GT check (`realcad/gt_check.json`, sheets from `realcad_gt_sheets.py`): 384 of 389 GT meshes match their prints.
`dev/00147363` has an extra thin rod (in the source cad_json) that the print lacks, so its scores are unreliable;
`test/00115681` is uncertain; `test/00147229` and `test/00446108` are not watertight (volume / IoU unreliable).

Check the layout: `python check_layout.py`.
Regenerate: `render_views.py <dev|test>` (DeepCAD), `render_fusion360.py split|render <dev|test>`; splits by `make_split.py`; shapes rebuilt by `cad_build.py`.
