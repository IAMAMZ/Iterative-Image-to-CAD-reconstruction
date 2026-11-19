"""Image-only inputs for multi-view reconstruction (VGGT / Depth Anything 3) of the RealCAD photos.

  python prep_realcad_recon_inputs.py --split test --n 50 [--size 518] [--out ../out/realcad_recon_in.zip]

Per part: the SAM 3 masks (image-only) cut the part out, the background becomes white, and all views are cropped
with ONE shared square box (union of the masks + 30 % margin, kept inside the photo) and resized to size x size.
The camera did not move between the photos (the part was turned on the table), so a shared crop keeps one
consistent pinhole camera, and with the static background removed the turning part looks like a camera orbiting
a fixed part, which is what multi-view models expect. Views whose mask is empty are left out.

zip layout: realcad_recon/ids.txt, realcad_recon/crops.json, realcad_recon/images/<id>/<view>.png
crops.json: {id: {"box": [x0, y0, side] in the 1024x768 photo, "size": size, "views": [kept views]}}
"""
import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
RC = HERE / "realcad"


def crop_box(masks, W, H, margin=0.3):
    ys, xs = np.nonzero(np.any(np.stack(masks), 0))
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    side = min(max(np.ptp(xs), np.ptp(ys)) * (1 + 2 * margin), H, W)
    x0 = int(round(min(max(cx - side / 2, 0), W - side)))
    y0 = int(round(min(max(cy - side / 2, 0), H - side)))
    return x0, y0, int(side)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--size", type=int, default=518)
    ap.add_argument("--out", default=str(HERE.parent / "out" / "realcad_recon_in.zip"))
    a = ap.parse_args()
    ids = [l.strip().split("/")[-1] for l in (RC / a.split / "ids.txt").read_text().split() if l.strip()][:a.n]
    crops, kept = {}, []
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_STORED) as z:
        for pid in ids:
            d = RC / a.split / "images" / pid
            rgb = {k: np.asarray(Image.open(d / "rgb" / f"{k}.jpg").convert("RGB")) for k in (1, 2, 3, 4)}
            msk = {k: np.asarray(Image.open(d / "mask" / f"{k}.png").convert("L")) > 127 for k in (1, 2, 3, 4)}
            views = [k for k in (1, 2, 3, 4) if msk[k].any()]
            if not views:
                continue
            H, W = msk[views[0]].shape
            x0, y0, side = crop_box([msk[k] for k in views], W, H)
            for k in views:
                im = np.where(msk[k][..., None], rgb[k], 255).astype(np.uint8)
                im = Image.fromarray(im).crop((x0, y0, x0 + side, y0 + side)).resize((a.size, a.size), Image.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, "PNG")
                z.writestr(f"realcad_recon/images/{pid}/{k}.png", buf.getvalue())
            crops[pid] = {"box": [x0, y0, side], "size": a.size, "views": views, "photo_wh": [W, H]}
            kept.append(pid)
        z.writestr("realcad_recon/ids.txt", "\n".join(kept) + "\n")
        z.writestr("realcad_recon/crops.json", json.dumps(crops, indent=1))
    (Path(a.out).with_suffix(".crops.json")).write_text(json.dumps(crops, indent=1))
    print(f"{len(kept)} parts, {sum(len(c['views']) for c in crops.values())} views -> {a.out}")


if __name__ == "__main__":
    main()
