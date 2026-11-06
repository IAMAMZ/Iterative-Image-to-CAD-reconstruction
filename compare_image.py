"""Image-mode checker: score a candidate part against a target *image* (no 3D target).

At test time there is only a picture of the part. This compares the candidate's
silhouette with the part's silhouette in that picture:

  1. target mask: from the image's alpha channel, a black/white mask image, or by
     separating the part from a plain background (colour of the image border).
     Real photos with clutter need a proper segmentation model first.
  2. camera: either a known rig camera (--camera front) or unknown
     (--camera search): try viewing directions on a grid, then refine the best ones.
     Cameras stay upright (no roll), as in the rig.
  3. size/position: one image can't tell absolute size or distance, so the candidate
     silhouette is shifted and scaled to the target's centre and area before
     scoring. Only the *shape* is judged.

    uv run python generate_solid.py guess.py --out out/guess
    uv run python compare_image.py photo.png out/guess --camera search
        -> out/guess/compare_image/{overlay.png, summary.png, report.json}

Overlay colours are as in compare.py: grey = both, RED = missing (in the image, not
the candidate), BLUE = extra (candidate only). There is no depth error here: a single
image has no depth. (compare.py does the full 3D-vs-3D check when a target model exists.)
"""
import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

from compare import BG, overlay_image
from cq_render import CQRenderer
from rig import _pose, load_rig, normalize

SEARCH_RES = 128


# ------------------------------------------------------------------ target mask
def target_mask(path: Path, tol=30):
    """-> (mask bool HxW, rgb uint8 HxWx3) from an image of the part."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") and np.asarray(im)[..., -1].min() < 255:
        a = np.asarray(im)[..., -1]
        return a > 127, np.asarray(im.convert("RGB"))
    rgb = np.asarray(im.convert("RGB"))
    g = np.asarray(im.convert("L"))
    if set(np.unique(g)) <= {0, 255}:                  # already a black/white mask
        return g > 127, rgb
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float64)
    bg = np.median(border, axis=0)                     # plain background colour
    dist = np.linalg.norm(rgb.astype(np.float64) - bg, axis=-1)
    return dist > tol, rgb


# ------------------------------------------------------------------ 2D alignment
def _moments(mask):
    ys, xs = np.nonzero(mask)
    return xs.mean(), ys.mean(), len(xs)


def warp(img, s, src_c, dst_c, shape, resample=Image.NEAREST, fill=BG):
    """Scale img by s about src_c and move src_c to dst_c, output of size shape (H, W)."""
    a = 1.0 / s
    coeffs = (a, 0, src_c[0] - dst_c[0] * a, 0, a, src_c[1] - dst_c[1] * a)
    pil = Image.fromarray(img.astype(np.uint8) * (255 if img.dtype == bool else 1))
    out = np.asarray(pil.transform((shape[1], shape[0]), Image.AFFINE, coeffs, resample,
                                   fillcolor=0 if img.dtype == bool else fill))
    return out > 127 if img.dtype == bool else out


def align(mask_t, mask_c):
    """Similarity (scale + shift) taking the candidate silhouette onto the target's."""
    cxt, cyt, nt = _moments(mask_t)
    cxc, cyc, nc = _moments(mask_c)
    return {"scale": math.sqrt(nt / nc), "src": (cxc, cyc), "dst": (cxt, cyt)}


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


# ------------------------------------------------------------------ scoring
class Scorer:
    """Renders the (normalised) candidate mesh from any viewing direction and scores it."""

    def __init__(self, mesh, rig, mask_t, res):
        self.mesh, self.rig = mesh, rig
        h, w = mask_t.shape
        k = res / max(h, w)
        self.size = (max(1, round(w * k)), max(1, round(h * k)))
        self.mask_t = np.asarray(Image.fromarray(mask_t.astype(np.uint8) * 255)
                                 .resize(self.size, Image.NEAREST)) > 127
        self.r = CQRenderer(*self.size)
        self.cache = {}

    def render(self, azim, elev):
        pose = _pose(azim, elev, self.rig["distance"])
        return self.r.render_pose(self.mesh, pose, self.rig["znear"], self.rig["zfar"],
                                  math.radians(self.rig["yfov_deg"]))

    def score(self, azim, elev):
        key = (round(azim % 360, 3), round(elev, 3))
        if key not in self.cache:
            _, _, mc = self.render(azim, elev)
            if not mc.any():
                self.cache[key] = 0.0
            else:
                al = align(self.mask_t, mc)
                self.cache[key] = iou(self.mask_t, warp(mc, al["scale"], al["src"], al["dst"],
                                                        self.mask_t.shape))
        return self.cache[key]

    def close(self):
        self.r.close()


def search_pose(scorer, coarse_step=15, keep=4):
    """Grid over azimuth x elevation, then hill-climb from the best few."""
    grid = [(a, e) for a in range(-180, 180, coarse_step) for e in range(-75, 91, coarse_step)]
    ranked = sorted(grid, key=lambda p: -scorer.score(*p))
    seeds, results = [], []
    for p in ranked:  # distinct seeds, so symmetric look-alikes are reported separately
        if all(abs((p[0] - q[0] + 180) % 360 - 180) > coarse_step or abs(p[1] - q[1]) > coarse_step
               for q in seeds):
            seeds.append(p)
        if len(seeds) == keep:
            break
    for a, e in seeds:
        best = scorer.score(a, e)
        for step in (coarse_step / 2, coarse_step / 6, coarse_step / 15):
            improved = True
            while improved:
                improved = False
                for da, de in itertools.product((-step, 0, step), repeat=2):
                    na, ne = a + da, float(np.clip(e + de, -90, 90))
                    s = scorer.score(na, ne)
                    if s > best + 1e-9:
                        best, a, e, improved = s, na, ne, True
        r = {"azim_deg": round(((a + 180) % 360) - 180, 2), "elev_deg": round(e, 2),
             "iou": round(best, 4)}
        # different seeds can climb to the same pose: keep it once
        if all(abs((r["azim_deg"] - q["azim_deg"] + 180) % 360 - 180) > 3 or
               abs(r["elev_deg"] - q["elev_deg"]) > 3 for q in results):
            results.append(r)
    return sorted(results, key=lambda r: -r["iou"])


# ------------------------------------------------------------------ main entry
def compare_image(target_img: Path, cand_dir: Path, out: Path, camera="search", rig=None):
    rig = rig or load_rig()
    mask_t, rgb_t = target_mask(target_img)
    if not mask_t.any():
        raise ValueError(f"found no part in {target_img} (background only?)")
    mesh, _, _ = normalize(trimesh.load(cand_dir / "solid.stl", force="mesh"))

    if camera == "search":
        sc = Scorer(mesh, rig, mask_t, SEARCH_RES)
        try:
            poses = search_pose(sc)
        finally:
            sc.close()
        azim, elev = poses[0]["azim_deg"], poses[0]["elev_deg"]
    else:
        cams = {c["name"]: c for c in rig["cameras"]}
        if camera not in cams:
            raise ValueError(f"unknown camera {camera!r}; rig has {sorted(cams)} (or 'search')")
        azim, elev, poses = cams[camera]["azim_deg"], cams[camera]["elev_deg"], None

    # final render and score at the target image's own resolution
    full = Scorer(mesh, rig, mask_t, max(mask_t.shape))
    try:
        rgb_c, _, mask_c = full.render(azim, elev)
    finally:
        full.close()
    if not mask_c.any():
        raise ValueError("candidate is not visible from this camera")
    al = align(mask_t, mask_c)
    mask_ca = warp(mask_c, al["scale"], al["src"], al["dst"], mask_t.shape)
    rgb_ca = warp(rgb_c, al["scale"], al["src"], al["dst"], mask_t.shape, Image.BILINEAR,
                  fill=tuple(int(v) for v in rgb_c[0, 0]))
    score = iou(mask_t, mask_ca)

    out.mkdir(parents=True, exist_ok=True)
    ov = overlay_image(mask_t, mask_ca)
    Image.fromarray(ov).save(out / "overlay.png")
    tiles = [(rgb_t, "target image"), (rgb_ca, f"candidate (az {azim:g}, el {elev:g})"),
             (ov, f"IoU {score:.3f}  red=missing blue=extra")]
    h, w = mask_t.shape
    sheet = Image.new("RGB", (3 * w, h), BG)
    for i, (img, txt) in enumerate(tiles):
        im = Image.fromarray(img)
        ImageDraw.Draw(im).text((6, 5), txt, fill=(0, 0, 0))
        sheet.paste(im, (i * w, 0))
    sheet.save(out / "summary.png")

    report = {
        "target_image": str(target_img), "candidate": str(cand_dir), "mode": camera,
        "iou": score, "camera": {"azim_deg": azim, "elev_deg": elev},
        "alignment": {"scale": al["scale"], "shift_px": [al["dst"][0] - al["src"][0] * al["scale"],
                                                        al["dst"][1] - al["src"][1] * al["scale"]]},
        "missing_px": int((mask_t & ~mask_ca).sum()), "extra_px": int((mask_ca & ~mask_t).sum()),
        # other poses that explain the image almost as well (symmetric parts look alike)
        "pose_candidates": poses,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image", type=Path, help="target image (photo/render, or a mask)")
    ap.add_argument("candidate", type=Path, help="generate_solid.py output dir of the candidate")
    ap.add_argument("--camera", default="search", help="rig camera name, or 'search' (default)")
    ap.add_argument("--out", type=Path, default=None, help="default: <candidate>/compare_image")
    args = ap.parse_args()
    r = compare_image(args.image, args.candidate, args.out or args.candidate / "compare_image",
                      args.camera)
    c = r["camera"]
    print(f"IoU {r['iou']:.3f}  camera az {c['azim_deg']:g} el {c['elev_deg']:g}  "
          f"missing {r['missing_px']} px, extra {r['extra_px']} px")
    if r["pose_candidates"] and len(r["pose_candidates"]) > 1:
        print("other poses that fit:", ", ".join(
            f"(az {p['azim_deg']:g}, el {p['elev_deg']:g}) {p['iou']:.3f}" for p in r["pose_candidates"][1:]))


if __name__ == "__main__":
    main()
