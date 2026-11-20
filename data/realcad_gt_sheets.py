"""Contact sheets to check the RealCAD ground-truth meshes against the photographed prints.

  python realcad_gt_sheets.py [--jobs 8] [--out ../out/gt_check]

For every part in dev + test: photo 1 and 3 next to the GT mesh (data/realcad/<split>/meshes/<id>.stl) rendered
from two corners above and one below, 20 parts per sheet. Uses cadrille/run_one.render_view (numpy z-buffer, no GPU / GL).
Also writes gt_stats.csv with simple shape stats (extents, bbox fill, bodies) to help spot odd meshes.
"""
import argparse
import csv
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "cadrille"))
from run_one import render_view  # noqa: E402

RC = HERE / "realcad"
T = 150
VIEWS = ([1, -1, -0.8], [-1, 1, -0.8], [1, 1, 0.8])   # view dirs in CAD z-up (z<0 = looking down): 2 above, 1 below


def unit(m):
    m = m.copy()
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    m.apply_scale(1.0 / m.extents.max())
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def tile(job):
    split, pid = job
    m = trimesh.load(RC / split / "meshes" / f"{pid}.stl")
    stats = {"split": split, "id": pid, "bodies": len(m.split()),
             "ext_sorted": "x".join(f"{v:.2f}" for v in sorted(m.extents / m.extents.max(), reverse=True)),
             "bbox_fill": round(float(m.volume / np.prod(m.extents)), 3)}
    u = unit(m)
    # z-up CAD: render_view uses y as image-up, so rotate z -> y
    u.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0], [0.5, 0.5, 0.5]))
    ims = []
    for k in (1, 3):
        ph = Image.open(RC / split / "images" / pid / "rgb" / f"{k}.jpg").convert("RGB")
        ph = ph.crop(((ph.width - ph.height) // 2, 0, (ph.width + ph.height) // 2, ph.height)).resize((T, T))
        ims.append(ph)
    for f in VIEWS:
        f = np.array([f[0], -f[2], f[1]], float)   # into the rotated (y-up) frame, looking down: y component < 0
        f /= np.linalg.norm(f)   # render_view needs a unit vector (it does not normalise; else the image is stretched)
        ims.append(render_view(u, f, distance=2.6, fov_deg=32, size=T * 2).resize((T, T), Image.LANCZOS))
    t = Image.new("RGB", (5 * T, T + 14), "white")
    for i, im in enumerate(ims):
        t.paste(im, (i * T, 14))
    ImageDraw.Draw(t).text((2, 1), f"{split}/{pid}  bodies {stats['bodies']}  fill {stats['bbox_fill']}", fill="black")
    return t, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", default=str(HERE.parent / "out" / "gt_check"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(s, l.strip().split("/")[-1]) for s in ("dev", "test", "test50")
            for l in (RC / s / "ids.txt").read_text().split() if l.strip()]
    with Pool(a.jobs) as p:
        res = p.map(tile, jobs, chunksize=4)
    per = 20
    for s in range(0, len(res), per):
        chunk = res[s:s + per]
        sheet = Image.new("RGB", (2 * 5 * T + 20, ((len(chunk) + 1) // 2) * (T + 18)), "white")
        for i, (t, _) in enumerate(chunk):
            sheet.paste(t, ((i % 2) * (5 * T + 20), (i // 2) * (T + 18)))
        sheet.save(out / f"sheet_{s // per:02d}.jpg", quality=88)
    with open(out / "gt_stats.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(res[0][1]))
        w.writeheader()
        w.writerows(r[1] for r in res)
    print(f"{len(res)} parts -> {(len(res) + per - 1) // per} sheets in {out}")


if __name__ == "__main__":
    main()
