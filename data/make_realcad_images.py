"""Make the tracked RealCAD input photos: downscaled copies of the full-resolution originals.

  python make_realcad_images.py [--max-side 1024] [--quality 90]

reads   data/realcad/<split>/ids.txt and the originals data/realcad/src/cad_real/<group>/<id>/{1..4}.jpg
        (full resolution, ~2 MB each, git-ignored -- see data/README.md for where to get them)
writes  data/realcad/<split>/images/<id>/rgb/{1..4}.jpg   (long side <= max-side; EXIF rotation applied)

Each output is written to a temp file and swapped in, so it never edits the original through a hard link.
"""
import argparse
import os
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).parent
RC = HERE / "realcad"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--quality", type=int, default=90)
    a = ap.parse_args()
    n = 0
    for split in ("dev", "test", "test50"):
        for pid in (l.strip() for l in (RC / split / "ids.txt").read_text().split() if l.strip()):
            part = pid.split("/")[-1]
            for k in (1, 2, 3, 4):
                src = RC / "src" / "cad_real" / pid / f"{k}.jpg"
                dst = RC / split / "images" / part / "rgb" / f"{k}.jpg"
                if not src.exists():
                    raise SystemExit(f"original missing: {src} (download RealCAD into data/realcad/src first)")
                im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
                im.thumbnail((a.max_side, a.max_side), Image.LANCZOS)
                tmp = dst.with_suffix(".tmp.jpg")
                dst.parent.mkdir(parents=True, exist_ok=True)
                im.save(tmp, "JPEG", quality=a.quality, optimize=True)
                os.replace(tmp, dst)   # new inode: breaks any hard link to src
                n += 1
        print(split, "done", flush=True)
    print(f"wrote {n} images")


if __name__ == "__main__":
    main()
