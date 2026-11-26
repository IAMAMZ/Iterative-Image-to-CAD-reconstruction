"""Build refine.py targets from a RealCAD photo split (default: test50_gt95).

    python data/realcad_targets.py                          # all 32 parts of test50_gt95
    python data/realcad_targets.py --ids 00000797 --force   # one part

reads   data/realcad/<split>/images/<id>/{rgb/<v>.jpg, mask/<v>.png, depth.npz}
        data/realcad/<split>/poses/<id>.json, meshes/<id>.stl   (metres)
writes  data/generated/targets/realcad_<split>/<id>/  laid out like a generate_solid.py output
        (layout.py), with the part's OWN 4 cameras instead of the fixed rig.json:
          internal/rig.json       the 4 photo cameras (refine.py / generate_solid.py --like use it,
                                  so candidates are rendered from exactly these cameras)
          renders/v<k>.png        the photo, cropped to a square around the part  (what the agent sees)
          renders/v<k>_mask.png   the SAM mask, same crop    (the target silhouette; mask_source=png)
          renders/v<k>_depth.png  preview of the depth map
          internal/depth.npz      the split's depth, same crop (normalised units; 0 = unknown)
          internal/info.json      frame, views, where each camera is (view_desc, for the prompts)
          gt.stl                  the true shape in mm, for offline scoring only

Frame: the split's poses are in "CAD axes; p = (p_cad - centre) * scale". The meshes are in
metres; targets are in mm (centre * 1000, scale / 1000), so the agent works in mm and the
normalised frame (cameras, depth) is unchanged.
Crop: per view, a square around the SAM mask's bounding box (+ --pad on each side), resized
to --size px; K is shifted and scaled with it (pixel-edge convention, as the poses use:
cx = W/2 is the image centre). Uses only the mask, never the GT, to place the crop.

With test50_gt / test50_gt95 the cameras and depth come from the GT CAD fit: an upper bound,
not an image-only input (see data/README.md).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import layout  # noqa: E402
from generate_solid import depth_preview  # noqa: E402

DEFAULT_SPLIT = ROOT / "data" / "realcad" / "test50_gt95"
MM_PER_M = 1000.0


# ------------------------------------------------------------------ geometry
def crop_box(mask: np.ndarray, pad: float):
    """Square (x0, y0, side) in photo pixels around the mask, `pad` x its size on each side."""
    rr, cc = np.nonzero(mask)
    if not len(rr):
        raise ValueError("empty mask")
    y0, y1, x0, x1 = rr.min(), rr.max() + 1, cc.min(), cc.max() + 1
    side = max(y1 - y0, x1 - x0) * (1 + 2 * pad)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return cx - side / 2, cy - side / 2, side


def crop_K(K, x0, y0, side, size):
    s = size / side
    K = np.asarray(K, np.float64)
    return [[K[0, 0] * s, 0.0, (K[0, 2] - x0) * s],
            [0.0, K[1, 1] * s, (K[1, 2] - y0) * s],
            [0.0, 0.0, 1.0]]


def crop(im: Image.Image, x0, y0, side, size, resample, fill):
    return im.transform((size, size), Image.EXTENT, (x0, y0, x0 + side, y0 + side),
                        resample=resample, fillcolor=fill)


def _axes(v, thresh=0.4):
    """Unit vector -> its main CAD axes, strongest first, at most 2: "+X-Y" or "+Z"."""
    order = np.argsort(-np.abs(v))
    parts = [f"{'+' if v[i] > 0 else '-'}{'XYZ'[i]}" for i in order[:2]
             if i == order[0] or abs(v[i]) >= thresh]
    return "".join(parts)


def view_desc(cam) -> str:
    """Where one camera is, in the part's CAD axes (vlm.photo_views_text builds the prompt)."""
    P = np.asarray(cam["pose_c2w"])
    d = P[:3, 3] / np.linalg.norm(P[:3, 3])              # part (origin) -> camera
    elev = math.degrees(math.asin(np.clip(d[2], -1, 1)))
    return (f"seen from {_axes(d)}, {elev:.0f} deg above the XY plane; "
            f"image right ~ {_axes(P[:3, 0])}, image up ~ {_axes(P[:3, 1])}")


# ------------------------------------------------------------------ build
def build_target(part: str, split: Path, out_root: Path, size=512, pad=0.3) -> dict:
    pose = json.loads((split / "poses" / f"{part}.json").read_text())
    img_dir = split / "images" / part
    depth_src = np.load(img_dir / "depth.npz")
    keys = sorted(pose["views"], key=int)

    out = out_root / part
    rd, idir = out / layout.RENDERS, out / layout.INTERNAL
    rd.mkdir(parents=True, exist_ok=True)
    idir.mkdir(parents=True, exist_ok=True)

    cams, depths, crops = [], {}, {}
    dists = []
    for k in keys:
        name = f"v{k}"
        v = pose["views"][k]
        mask = Image.open(img_dir / "mask" / f"{k}.png").convert("L")
        x0, y0, side = crop_box(np.asarray(mask) > 127, pad)
        crops[name] = {"x0": x0, "y0": y0, "side": side, "photo": k}
        rgb = Image.open(img_dir / "rgb" / f"{k}.jpg").convert("RGB")
        crop(rgb, x0, y0, side, size, Image.BICUBIC, (128, 128, 128)).save(rd / f"{name}.png")
        m = crop(mask, x0, y0, side, size, Image.BILINEAR, 0)
        m.point(lambda p: 255 if p > 127 else 0).save(rd / f"{name}_mask.png")
        dep = Image.fromarray(depth_src[k].astype(np.float32), mode="F")
        dep = np.asarray(crop(dep, x0, y0, side, size, Image.NEAREST, 0.0), np.float32)
        depths[name] = dep
        Image.fromarray(depth_preview(dep)).save(rd / f"{name}_depth.png")
        c2w = np.asarray(v["c2w"], np.float64)
        dists.append(float(np.linalg.norm(c2w[:3, 3])))
        cams.append({"name": name, "photo": k, "pose_c2w": c2w.tolist(),
                     "K": crop_K(v["K"], x0, y0, side, size)})
    np.savez_compressed(idir / "depth.npz", **depths)

    K0 = cams[0]["K"]
    rig = {"convention": "per-part photo cameras (RealCAD); part normalised as in info.json; "
                         "pose_c2w is OpenGL camera-to-world; K per camera, OpenCV pixel "
                         "intrinsics of the cropped image (pixel-edge convention)",
           "width": size, "height": size,
           "yfov_deg": math.degrees(2 * math.atan(size / 2 / K0[1][1])),
           "znear": max(0.05, min(dists) - 1.5), "zfar": max(dists) + 1.5,
           "K": K0, "cameras": cams}
    (idir / "rig.json").write_text(json.dumps(rig, indent=2) + "\n")

    mesh = trimesh.load(split / "meshes" / f"{part}.stl", force="mesh")
    mesh.apply_scale(MM_PER_M)
    mesh.export(out / "gt.stl")
    names = [c["name"] for c in cams]
    info = {"source": f"realcad/{split.name}", "part": part, "units": "mm",
            "normalization": {"center": (np.asarray(pose["centre"]) * MM_PER_M).tolist(),
                              "scale": float(pose["scale"]) / MM_PER_M},
            "views": names, "grid_views": names[:4], "mask_source": "png",
            "view_desc": {c["name"]: view_desc(c) for c in cams[:4]},
            "bbox_min": mesh.bounds[0].tolist(), "bbox_max": mesh.bounds[1].tolist(),
            "crop": crops, "crop_size": size, "crop_pad": pad,
            "uses_ground_truth": "GT CAD" in pose.get("source", ""),
            "gt_watertight": bool(mesh.is_watertight)}
    (idir / "info.json").write_text(json.dumps(info, indent=2) + "\n")
    return info


def read_ids(split: Path):
    return [l.strip().split("/")[-1] for l in (split / "ids.txt").read_text().split() if l.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", type=Path, default=DEFAULT_SPLIT, help="data/realcad/<split> dir")
    ap.add_argument("--out", type=Path, default=None,
                    help="default: data/generated/targets/realcad_<split name>")
    ap.add_argument("--ids", nargs="*", default=None, help="only these part ids")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--size", type=int, default=512, help="crop size in px")
    ap.add_argument("--pad", type=float, default=0.3, help="crop margin, x the part's size per side")
    ap.add_argument("--force", action="store_true", help="rebuild targets that already exist")
    args = ap.parse_args()
    out = args.out or ROOT / "data" / "generated" / "targets" / f"realcad_{args.split.name}"
    parts = args.ids or read_ids(args.split)[:args.limit]
    done = failed = 0
    for p in parts:
        if layout.info(out / p).exists() and not args.force:
            continue
        try:
            build_target(p, args.split, out, args.size, args.pad)
            done += 1
        except Exception as e:  # keep going; report at the end
            failed += 1
            print(f"{p}: {type(e).__name__}: {e}", file=sys.stderr)
    print(f"built {done} targets in {out} ({failed} failed, {len(parts) - done - failed} already there)")


if __name__ == "__main__":
    main()
