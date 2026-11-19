"""Turn the raw VGGT output (image-only) into RealCAD dataset files: cameras, intrinsics and depth per photo.

  python convert_realcad_vggt.py --zip ../out/realcad_recon_vggt.zip [--split test50] [--crops ../out/realcad_recon_in.crops.json]

Uses only what VGGT predicted from the 4 masked photos plus the SAM 3 masks: no CAD, no GT.
writes  data/realcad/<split>/poses/<id>.json          cameras (OpenGL camera-to-world) + intrinsics per view
        data/realcad/<split>/images/<id>/depth.npz    z-depth per view ('1'..'4'), full photo size, 0 = no depth
        data/realcad/<split>/images/<id>/depth_conf.npz  VGGT confidence for the same pixels (0 = none)

Object frame (built from the prediction itself):
  +Z  = the axis the part was turned about between photos (table normal), from the relative camera rotations,
        signed so the camera is above the table
  +X  = horizontal direction towards the camera of the first kept view; +Y = Z x X
  origin / scale = bbox centre and bounding-sphere radius of the fused VGGT point cloud (high-confidence pixels,
        0.5 % outliers trimmed), so the part sits in a unit sphere like the synthetic sets
Intrinsics: VGGT's crop intrinsics mapped back to the 1024 x 768 photo (crop offset + scale).
Depth: VGGT depth resized from the 518 crop into its box in the photo, kept inside the SAM mask, in object units.
"""
import argparse
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
RC = HERE / "realcad"
OUT = HERE.parent / "out"
CV2GL = np.diag([1.0, -1.0, -1.0, 1.0])


def rot_axis_angle(R):
    ang = math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2)))
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    n = np.linalg.norm(ax)
    return (ax / n if n > 1e-9 else np.zeros(3)), ang


def convert_part(pid, pred, crop, split, elev_prior=None):
    views = [int(v) for v in pred["views"]]
    E = pred["extrinsics"].astype(np.float64)                 # (V,3,4) world -> camera (OpenCV)
    Kc = pred["intrinsics"].astype(np.float64)                # crop pixels
    dep = pred["depth"].astype(np.float32)                    # (V,h,w) crop
    conf = pred["conf"].astype(np.float32)
    h, w = dep.shape[-2:]
    x0, y0, side = crop["box"]
    W, H = crop.get("photo_wh", [1024, 768])
    s_img = side / w
    Rw2c = [E[i, :, :3] for i in range(len(views))]
    C = np.array([-E[i, :, :3].T @ E[i, :, 3] for i in range(len(views))])

    # SAM masks: full res and in the crop
    m_full = {k: np.asarray(Image.open(RC / split / "images" / pid / "mask" / f"{k}.png").convert("L")) > 127
              for k in views}
    m_crop = {k: np.asarray(Image.fromarray(m_full[k].astype(np.uint8) * 255)
                            .crop((x0, y0, x0 + side, y0 + side)).resize((w, h), Image.NEAREST)) > 127 for k in views}

    # fused point cloud (high-confidence masked pixels)
    vv, uu = np.mgrid[:h, :w]
    pts = []
    for i, k in enumerate(views):
        ok = m_crop[k] & (dep[i] > 0)
        if ok.sum() == 0:
            continue
        ok &= conf[i] >= np.percentile(conf[i][ok], 25)
        ray = np.linalg.inv(Kc[i]) @ np.stack([uu[ok] + 0.5, vv[ok] + 0.5, np.ones(ok.sum())])
        pts.append((Rw2c[i].T @ (ray * dep[i][ok] - E[i, :, 3:4])).T)
    P = np.concatenate(pts)

    # up axis = turning axis of the cameras around the part
    axes = []
    for i in range(len(views)):
        for j in range(i + 1, len(views)):
            ax, ang = rot_axis_angle(Rw2c[j].T @ Rw2c[i])        # camera i -> camera j, in world coords
            if ang > math.radians(15):
                axes.append(ax if not axes or ax @ axes[0] >= 0 else -ax)
    degenerate = not axes or elev_prior is not None
    if axes and elev_prior is None:
        up = np.mean(axes, 0)
        up /= np.linalg.norm(up)
        if ((C - P.mean(0)) @ up).mean() < 0:                   # camera is above the table
            up = -up
    else:
        # the cameras did not turn (one view, or a symmetric part that looks the same from every side):
        # tilt camera 0's 'up' by the typical elevation measured on the consistent parts
        e = math.radians(elev_prior if elev_prior is not None else 44.0)
        f, u = Rw2c[0][2], -Rw2c[0][1]                           # viewing direction, image-up (world coords)
        up = math.cos(e) * u - math.sin(e) * f
        up /= np.linalg.norm(up)

    # object frame
    lo, hi = np.percentile(P, 0.5, axis=0), np.percentile(P, 99.5, axis=0)
    keep = np.all((P >= lo) & (P <= hi), axis=1)
    Pk = P[keep]
    c0 = Pk.mean(0)
    hor = (C[0] - c0) - ((C[0] - c0) @ up) * up
    xax = hor / np.linalg.norm(hor)
    yax = np.cross(up, xax)
    R_wo = np.stack([xax, yax, up])                              # world -> object rotation (rows = object axes)
    Q = (Pk - c0) @ R_wo.T
    centre_o = (Q.min(0) + Q.max(0)) / 2
    radius = float(np.linalg.norm(Q - centre_o, axis=1).max())
    scale = 1.0 / radius
    to_obj = lambda X: scale * ((X - c0) @ R_wo.T - centre_o)   # noqa: E731

    rec_views, depths, confs = {}, {}, {}
    for i, k in enumerate(views):
        c2w = np.eye(4)
        c2w[:3, :3] = R_wo @ Rw2c[i].T
        c2w[:3, 3] = to_obj(C[i][None])[0]
        c2w_gl = c2w @ CV2GL
        K = Kc[i].copy()
        K[0, 0] *= s_img
        K[1, 1] *= s_img
        K[0, 2] = x0 + K[0, 2] * s_img
        K[1, 2] = y0 + K[1, 2] * s_img
        cam = c2w[:3, 3]
        rec_views[str(k)] = {"c2w": c2w_gl.round(6).tolist(), "K": K.round(3).tolist(),
                             "elevation_deg": round(math.degrees(math.asin(cam[2] / np.linalg.norm(cam))), 2),
                             "azimuth_deg": round(math.degrees(math.atan2(cam[1], cam[0])), 2),
                             "distance": round(float(np.linalg.norm(cam)), 4)}
        # depth into the full photo (object units), inside the SAM mask only
        d_box = np.asarray(Image.fromarray(dep[i] * scale).resize((side, side), Image.BILINEAR))
        c_box = np.asarray(Image.fromarray(conf[i]).resize((side, side), Image.BILINEAR))
        D = np.zeros((H, W), np.float32)
        Cf = np.zeros((H, W), np.float32)
        D[y0:y0 + side, x0:x0 + side] = d_box
        Cf[y0:y0 + side, x0:x0 + side] = c_box
        D[~m_full[k]] = 0
        Cf[~m_full[k]] = 0
        depths[str(k)] = D.astype(np.float16)
        confs[str(k)] = Cf.astype(np.float16)
    missing = [k for k in (1, 2, 3, 4) if k not in views]
    el = np.array([v["elevation_deg"] for v in rec_views.values()])
    az = np.array([v["azimuth_deg"] for v in rec_views.values()])
    steps = [abs((b - a + 180) % 360 - 180) for a, b in zip(az[:-1], az[1:])]
    quality = {"n_views": len(views), "up_from": "camera turn axis" if not degenerate else "elevation prior",
               "elevation_std_deg": round(float(el.std()), 2),
               "azimuth_steps_deg": [round(x, 1) for x in steps]}
    # the rig turned the part on the table under a fixed camera: views should share one elevation
    quality["flag"] = ("inconsistent_views" if len(views) >= 2 and el.std() >= 5 else
                       "symmetric_or_single_view" if degenerate or len(views) < 2 else "ok")
    rec = {"id": pid, "split": split, "source": "VGGT-1B on the 4 photos cut out by their SAM 3 masks (no CAD, no GT)",
           "frame": "object frame from the prediction: +Z = axis the part was turned about (table normal, camera above), "
                    "+X = towards the first kept camera, origin = bbox centre of the fused point cloud, unit bounding "
                    "sphere; c2w = OpenGL camera-to-world; K in pixels of the 1024x768 photo; depth.npz = z along the "
                    "view axis in object units, 0 = no depth",
           "image_size": [W, H], "views": rec_views, "missing_views": missing, "quality": quality,
           "vggt_world_to_object": {"R": R_wo.round(6).tolist(), "c0": c0.round(6).tolist(),
                                    "centre": centre_o.round(6).tolist(), "scale": scale}}
    pdir = RC / split / "poses"
    pdir.mkdir(exist_ok=True)
    (pdir / f"{pid}.json").write_text(json.dumps(rec, indent=1))
    np.savez_compressed(RC / split / "images" / pid / "depth.npz", **depths)
    np.savez_compressed(RC / split / "images" / pid / "depth_conf.npz", **confs)
    return rec, to_obj(P)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(OUT / "realcad_recon_vggt.zip"))
    ap.add_argument("--split", default="test50")
    ap.add_argument("--crops", default=str(OUT / "realcad_recon_in.crops.json"))
    a = ap.parse_args()
    crops = json.loads(Path(a.crops).read_text())
    z = zipfile.ZipFile(a.zip)
    names = {Path(n).stem: n for n in z.namelist() if n.startswith("vggt/") and n.endswith(".npz")}
    recs = {}
    for pid in sorted(names):
        recs[pid], _ = convert_part(pid, np.load(io.BytesIO(z.read(names[pid]))), crops[pid], a.split)
    # elevation prior from the parts whose views agree (image-only), then redo the ones without a turn axis
    good = [np.mean([v["elevation_deg"] for v in r["views"].values()]) for r in recs.values() if r["quality"]["flag"] == "ok"]
    prior = float(np.median(good)) if good else 44.0
    for pid, r in recs.items():
        if r["quality"]["up_from"] == "elevation prior" or r["quality"]["n_views"] < 2 or                 np.mean([v["elevation_deg"] for v in r["views"].values()]) < 15:
            recs[pid], _ = convert_part(pid, np.load(io.BytesIO(z.read(names[pid]))), crops[pid], a.split, prior)
    for pid, r in recs.items():
        el = [v["elevation_deg"] for v in r["views"].values()]
        az = [v["azimuth_deg"] for v in r["views"].values()]
        print(f"{pid}  {r['quality']['flag']:24s} elev {np.round(el, 1).tolist()}  azim {np.round(az, 0).tolist()}")
    from collections import Counter
    print(f"converted {len(recs)} parts; elevation prior {prior:.1f} deg from {len(good)} consistent parts;",
          dict(Counter(r["quality"]["flag"] for r in recs.values())))


if __name__ == "__main__":
    main()
