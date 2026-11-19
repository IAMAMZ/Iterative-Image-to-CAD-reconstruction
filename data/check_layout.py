"""Check that data/ follows the standard layout:  python check_layout.py

data/<dataset>/<split>/ids.txt
                       images/<id>/rgb/<view>.(png|jpg)   4 views (+ mask/, depth.npz for synthetic renders)
                       poses/<id>.json                    deepcad, fusion360 (rendered); realcad test50 (VGGT, image-only)
                       meshes/<id>.stl                    hidden ground truth
datasets: deepcad, realcad, fusion360;  splits: dev, test (+ realcad test50: mask/, depth.npz, poses from the photos)
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
TABLE = ["top_back", "top_front", "top_left", "top_right"]
REAL = ["1", "2", "3", "4"]
SPEC = {"deepcad": dict(views=TABLE, ext="png", poses=True),
        "fusion360": dict(views=TABLE, ext="png", poses=True),
        "realcad": dict(views=REAL, ext="jpg", poses=False)}


def main():
    bad = 0
    for ds, spec in SPEC.items():
        for split in [s for s in ("dev", "test", "test50") if (HERE / ds / s / "ids.txt").exists()]:
            root = HERE / ds / split
            image_only = ds == "realcad" and split == "test50"   # masks + VGGT depth/poses, some views may be empty
            ids = [l.strip() for l in (root / "ids.txt").read_text().split() if l.strip()]
            parts = [i.split("/")[-1] for i in ids]
            miss = {"images": 0, "masks": 0, "depth": 0, "poses": 0, "meshes": 0}
            for p in parts:
                im = root / "images" / p
                if not all((im / "rgb" / f"{v}.{spec['ext']}").exists() for v in spec["views"]):
                    miss["images"] += 1
                if spec["poses"] or image_only:
                    if not all((im / "mask" / f"{v}.png").exists() for v in spec["views"]):
                        miss["masks"] += 1
                    d = im / "depth.npz"
                    if not d.exists() or not set(np.load(d).files) <= set(spec["views"]) or                             (not image_only and sorted(np.load(d).files) != sorted(spec["views"])):
                        miss["depth"] += 1
                    if not (root / "poses" / f"{p}.json").exists():
                        miss["poses"] += 1
                if not (root / "meshes" / f"{p}.stl").exists():
                    miss["meshes"] += 1
            if not spec["poses"] and not image_only:
                miss.pop("masks"), miss.pop("depth"), miss.pop("poses")
            ok = not any(miss.values())
            bad += not ok
            print(f"{ds:10s} {split:6s} {len(parts):5d} parts  {'OK' if ok else 'MISSING ' + str(miss)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
