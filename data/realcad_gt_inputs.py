"""Build data/realcad/<split>_gt: RealCAD with "free" perception -- SAM masks, depth and cameras from the GT CAD.

  python realcad_gt_inputs.py                                    # test50 -> test50_gt from ../out/pose_fit_v3
  python realcad_gt_inputs.py --fits <run> <run> ...             # several fit runs: best IoU per part
  python realcad_gt_inputs.py --subset 0.95                      # test50_gt -> test50_gt95: only the parts whose
                                                                 # cameras explain the SAM masks well (mean IoU >= 0.95)

RealCAD has no rendered ground truth, only the CAD mesh. fit_realcad_pose.py places that mesh in each photo (one fixed
camera, the part turned on the table between views) and rasterises it; this script copies the result into the same
layout as data/realcad/<split>, so every pipeline that reads <split> runs unchanged on <split>_gt:

  images/<id>/rgb/{1..4}.jpg   the real photos (copied)
  images/<id>/mask/{1..4}.png  the SAM 3 masks of <split> (taken as the true outline: they follow the photos more
                               closely than any CAD fit; holes kept, no empty views)
  images/<id>/depth.npz        z along the view axis of the posed GT mesh, object units, float16; kept only where the
                               SAM mask and the CAD silhouette agree, 0 elsewhere, so no point lands off the part
  poses/<id>.json              per view OpenGL camera-to-world + K (1024x768 photo pixels); one fitted focal per part
  meshes/<id>.stl/.step        GT (copied)
  gt_fit_qa.csv                per view: IoU of the CAD silhouette vs the SAM mask (how well the cameras explain
                               the photo), share of the mask that has depth, flags

Frame = the synthetic convention: CAD mesh moved to its bbox centre and scaled to a unit bounding sphere,
p = (p_cad - centre) * scale, axes = CAD axes (R_table = I). Unlike test50 (VGGT frame), it is the GT frame, so
"raw" scores are not penalised for orientation: report raw and aligned. table_up = table normal in this frame.

Uses the GT: an upper bound for the downstream CAD step, never an image-only input.
"""
import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from fit_realcad_pose import colour_mask

HERE = Path(__file__).parent
RC = HERE / "realcad"
VIEWS = ("1", "2", "3", "4")
FLAG_IOU = 0.85


def part_ids(split):
    return [l.strip().split("/")[-1] for l in (RC / split / "ids.txt").read_text().split() if l.strip()]


def targets(split, pid):
    """fit targets per view: SAM mask (holes kept), or the colour fallback where SAM found nothing"""
    out = {}
    for k in VIEWS:
        m = np.asarray(Image.open(RC / split / "images" / pid / "mask" / f"{k}.png").convert("L")) > 127
        src = "sam"
        if not m.any():
            m = colour_mask(np.asarray(Image.open(RC / split / "images" / pid / "rgb" / f"{k}.jpg").convert("RGB")))
            src = "colour"
        out[k] = (m, src)
    return out


def score_fit(fit_dir, tg):
    rows = []
    for k in VIEWS:
        sil = np.asarray(Image.open(fit_dir / "mask_cad" / f"{k}.png")) > 127
        t, src = tg[k]
        iou = float((sil & t).sum() / max((sil | t).sum(), 1))
        rows.append({"view": k, "target": src, "iou": round(iou, 4), "cad_area_frac": round(float(sil.mean()), 4)})
    return rows


def make_subset(split, thr):
    """copy the parts of <split>_gt whose mean CAD-vs-SAM IoU >= thr into <split>_gt<thr*100>, same layout"""
    src = RC / f"{split}_gt"
    dst = RC / f"{split}_gt{round(thr * 100)}"
    if dst.exists():
        shutil.rmtree(dst)
    lines = [l.strip() for l in (src / "ids.txt").read_text().split() if l.strip()]
    keep = [l for l in lines if json.loads((src / "poses" / f"{l.split('/')[-1]}.json").read_text())
            ["quality"]["mean_cad_mask_iou"] >= thr]
    (dst / "poses").mkdir(parents=True)
    (dst / "meshes").mkdir()
    for l in keep:
        pid = l.split("/")[-1]
        shutil.copytree(src / "images" / pid, dst / "images" / pid)
        shutil.copy(src / "poses" / f"{pid}.json", dst / "poses" / f"{pid}.json")
        for ext in ("stl", "step"):
            if (src / "meshes" / f"{pid}.{ext}").exists():
                shutil.copy(src / "meshes" / f"{pid}.{ext}", dst / "meshes" / f"{pid}.{ext}")
    (dst / "ids.txt").write_text("\n".join(keep) + "\n")
    ids = {l.split("/")[-1] for l in keep}
    with open(src / "gt_fit_qa.csv", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["id"] in ids]
    with open(dst / "gt_fit_qa.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    ious = [float(r["iou"]) for r in rows]
    print(f"{dst.name}: {len(keep)} of {len(lines)} parts (mean IoU >= {thr}); view IoU mean {np.mean(ious):.3f}, "
          f"median {np.median(ious):.3f}, min {min(ious):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test50")
    ap.add_argument("--fits", nargs="+", default=[str(HERE.parent / "out" / "pose_fit_v3")])
    ap.add_argument("--subset", type=float, help="only copy the well-fitted parts of <split>_gt (mean IoU >= this)")
    a = ap.parse_args()
    if a.subset is not None:
        return make_subset(a.split, a.subset)
    src, dst = RC / a.split, RC / f"{a.split}_gt"
    fit_roots = [Path(f) for f in a.fits]
    (dst / "poses").mkdir(parents=True, exist_ok=True)
    (dst / "meshes").mkdir(exist_ok=True)
    shutil.copy(src / "ids.txt", dst / "ids.txt")
    qa = []
    for pid in part_ids(a.split):
        tg = targets(a.split, pid)
        cands = []
        for root in fit_roots:
            if (root / pid / "pose.json").exists():
                rows = score_fit(root / pid, tg)
                cands.append((np.mean([r["iou"] for r in rows]), root, rows))
        if not cands:
            print(f"{pid}: no fit, skipped")
            continue
        mean_iou, root, rows = max(cands, key=lambda c: c[0])
        fit = json.loads((root / pid / "pose.json").read_text())

        im = dst / "images" / pid
        (im / "rgb").mkdir(parents=True, exist_ok=True)
        (im / "mask").mkdir(exist_ok=True)
        cad_depth = np.load(root / pid / "depth.npz")
        depth = {}
        for k, r in zip(VIEWS, rows):
            shutil.copy(src / "images" / pid / "rgb" / f"{k}.jpg", im / "rgb" / f"{k}.jpg")
            shutil.copy(src / "images" / pid / "mask" / f"{k}.png", im / "mask" / f"{k}.png")
            m = tg[k][0]
            d = cad_depth[k].copy()
            d[~m] = 0
            depth[k] = d
            r["depth_cover"] = round(float((d > 0).sum() / max(m.sum(), 1)), 4)   # share of the mask with depth
        np.savez_compressed(im / "depth.npz", **depth)
        for ext in ("stl", "step"):
            if (src / "meshes" / f"{pid}.{ext}").exists():
                shutil.copy(src / "meshes" / f"{pid}.{ext}", dst / "meshes" / f"{pid}.{ext}")

        R_rest = np.array(fit["R_rest"])                     # CAD axes -> table axes (table +Z up)
        up = R_rest.T @ np.array([0.0, 0.0, 1.0])
        rec = {"id": pid, "split": a.split,
               "source": "masks: SAM 3 (as in the image-only split); cameras + depth: GT CAD mesh fitted to those "
                         "masks (fit_realcad_pose.py), depth kept inside the mask; uses the ground truth",
               "frame": "CAD axes; p = (p_cad - centre) * scale (bbox centre, unit bounding sphere); c2w = OpenGL "
                        "camera-to-world; K in pixels of the 1024x768 photo; depth.npz = z along the view axis in "
                        "object units, 0 = background or outside the SAM mask",
               "centre": fit["centre"], "scale": fit["scale"], "R_table": np.eye(3).tolist(),
               "table_up": up.round(6).tolist(), "image_size": fit["image_size"],
               "camera": fit["camera"], "R_rest": fit["R_rest"],
               "views": {k: {"c2w": fit["views"][k]["c2w"], "K": fit["K"], "yaw_deg": fit["views"][k]["yaw_deg"],
                             "fit_target": r["target"], "cad_mask_iou": r["iou"], "depth_cover": r["depth_cover"]}
                         for k, r in zip(VIEWS, rows)},
               "quality": {"mean_cad_mask_iou": round(float(mean_iou), 4),
                           "min_cad_mask_iou": min(r["iou"] for r in rows),
                           "capture": fit.get("capture"),
                           "fit_run": root.name,
                           "flag": "ok" if min(r["iou"] for r in rows) >= FLAG_IOU else "check"}}
        (dst / "poses" / f"{pid}.json").write_text(json.dumps(rec, indent=1))
        for r in rows:
            qa.append({"id": pid, **r, "fit_run": root.name,
                       "flags": "" if r["iou"] >= FLAG_IOU else "low_iou"})
        print(f"{pid}: {root.name:15s} mean IoU {mean_iou:.3f}  min {rec['quality']['min_cad_mask_iou']:.3f}"
              f"  {rec['quality']['flag']}")
    with open(dst / "gt_fit_qa.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(qa[0]))
        w.writeheader()
        w.writerows(qa)
    ious = [r["iou"] for r in qa]
    print(f"{len(qa) // 4} parts, {len(qa)} views: median IoU {np.median(ious):.3f}, "
          f"{sum(i < FLAG_IOU for i in ious)} views < {FLAG_IOU}")


if __name__ == "__main__":
    main()
