# data/

Three datasets, each with a `dev` and a `test` split and the same layout:

```
data/<dataset>/<split>/
    ids.txt                       parts in the split
    images/<id>/rgb/<view>.png    the 4 input views (RealCAD: rgb/1.jpg .. 4.jpg, real photos)
    images/<id>/mask/<view>.png   synthetic datasets only
    images/<id>/depth.npz         synthetic datasets only (float16 depth per view)
    poses/<id>.json               synthetic datasets only: centre, scale, R_table (object pose), table info
    meshes/<id>.stl (.step)       hidden ground truth; *_table_posed.stl = GT in the render frame
    manifest.json                 synthetic datasets only: render log for the split
```

| dataset   | dev | test | images | poses | meshes | notes |
|-----------|----:|-----:|--------|-------|--------|-------|
| deepcad   | 100 | 100  | 4 table views (rendered) | yes | stl + step (built from `deepcad/cad_json`) | |
| fusion360 | 572 | 345 | 4 table views (rendered) | yes | stl | dev = former "train", trimmed to the 572 parts cadrille RL was run on (other 808 in `archive/fusion360_dev_unrun`); all parts come from `raw/fusion360_test_mesh` |
| realcad   | 100 | 289  | 4 real photos, downscaled to 1024 px (originals are 4032x3024) | none | stl + step (built from `realcad/cad_json`) | test = 100 seeded picks + the 189 other built meshes |

The 4 views are the "table" cameras of `cameras.json` (`top_left`, `top_right`, `top_front`, `top_back`).
The old 6 axis views are in `archive/` (git-ignored).

Everything here is tracked in git except two folders of original downloads and the git-ignored `archive/` at the repo root:

| not in git | what it is | how to get it |
|---|---|---|
| `realcad/src/` (3.3 GB) | full-resolution RealCAD photos, `src/cad_real/<group>/<id>/{1..4}.jpg` (4032x3024) | ask Metom for a copy and unpack it to that path. Only needed to regenerate the downscaled inputs with `python make_realcad_images.py` |
| `raw/` | Fusion360 source meshes `raw/fusion360_test_mesh` (Hugging Face `maksimko123/fusion360_test_mesh`) and DeepCAD json archives | only needed to re-render / rebuild; the renders, poses and meshes below are already tracked |

The RealCAD photos in `realcad/<split>/images/` are the tracked, downscaled inputs (long side 1024 px, made by `make_realcad_images.py`); the originals are not in git.

Check the layout: `python check_layout.py`.
Regenerate: `render_views.py <dev|test>` (DeepCAD), `render_fusion360.py split|render <dev|test>`; splits by `make_split.py`; shapes rebuilt by `cad_build.py`.
