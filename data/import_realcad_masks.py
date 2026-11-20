"""Import the SAM 3 masks made by sam3_realcad_masks.ipynb (Kaggle / Colab) into the RealCAD layout.

  python import_realcad_masks.py path/to/realcad_masks.zip --split dev
  python import_realcad_masks.py path/to/realcad_masks.zip --split test

reads   the zip: images/<id>/mask/{1..4}.png, mask_qa.csv, review/*.jpg
writes  data/realcad/<split>/images/<id>/mask/{1..4}.png   (0/255, same size as rgb/<view>.jpg)
        data/realcad/<split>/mask_qa.csv                   (per-photo prompt, score, area, flags)
Only entries matching those names are extracted; every part in <split>/ids.txt must get all 4 masks,
each the same size as its photo, or nothing is written.
"""
import argparse
import csv
import io
import re
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

RC = Path(__file__).parent / "realcad"
MASK_RE = re.compile(r"^(?:[^/]+/)?images/(\d{8})/mask/([1-4])\.png$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("zip")
    ap.add_argument("--split", default="test", choices=["dev", "test", "test50"])
    a = ap.parse_args()
    split = RC / a.split
    ids = [l.strip().split("/")[-1] for l in (split / "ids.txt").read_text().split() if l.strip()]
    z = zipfile.ZipFile(a.zip)

    masks, qa = {}, None
    for name in z.namelist():
        m = MASK_RE.match(name)
        if m and m.group(1) in ids:
            masks[(m.group(1), int(m.group(2)))] = name
        elif name.endswith("mask_qa.csv"):
            qa = name
    missing = [(i, k) for i in ids for k in (1, 2, 3, 4) if (i, k) not in masks]
    if missing:
        raise SystemExit(f"{len(missing)} masks missing, e.g. {missing[:5]} -- nothing written")

    loaded = {}
    for (pid, k), name in masks.items():
        im = Image.open(io.BytesIO(z.read(name))).convert("L")
        rgb = Image.open(split / "images" / pid / "rgb" / f"{k}.jpg")
        if im.size != rgb.size:
            raise SystemExit(f"{pid} view {k}: mask {im.size} != photo {rgb.size} -- nothing written")
        loaded[(pid, k)] = im.point(lambda v: 255 if v >= 128 else 0)

    for (pid, k), im in loaded.items():
        dst = split / "images" / pid / "mask" / f"{k}.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst)
    print(f"wrote {len(loaded)} masks for {len(ids)} parts into {split / 'images'}")

    if qa:
        rows = [r for r in csv.DictReader(io.StringIO(z.read(qa).decode())) if r["id"] in ids]   # zip may hold both splits
        with open(split / "mask_qa.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        flags = Counter(f for r in rows for f in r["flags"].split())
        n_flag = sum(bool(r["flags"]) for r in rows)
        print(f"mask_qa.csv: {n_flag}/{len(rows)} photos flagged {dict(flags)}")
        worst = sorted(rows, key=lambda r: float(r["best_score"]))[:10]
        print("lowest-score photos:", ", ".join(f"{r['id']}/{r['view']} ({r['best_score']})" for r in worst))


if __name__ == "__main__":
    main()
