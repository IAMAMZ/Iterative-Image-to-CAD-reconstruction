"""Score image-only multi-view reconstructions (VGGT / Depth Anything 3) of RealCAD against the GT-fit reference.

  python eval_realcad_recon.py --zip ../out/realcad_recon_vggt.zip --model vggt
  python eval_realcad_recon.py --zip ../out/realcad_recon_da3.zip  --model da3

Prediction (from the photos only): <model>/<id>.npz with views, extrinsics (V,3,4 OpenCV world-to-camera),
intrinsics (V,3,3 in pixels of the hw crop), depth (V,H,W), conf; crops from out/realcad_recon_in.crops.json.
Reference (uses the GT CAD, so only for scoring): out/pose_fit/<id>/pose.json + depth.npz from data/fit_realcad_pose.py.

Metrics per part
  rot_err_deg   relative rotation error over all view pairs (frame-free): angle(R_i R_j^T vs ref)
  focal_err_%   predicted focal (converted to full-photo px) vs the reference focal
  depth_absrel  |s*d_pred - d_ref| / d_ref over pixels inside the SAM mask where both exist, one scale s per part
                (median ratio over all views): depth up to scale, as the models only know scale up to a factor
  chamfer       the predicted point cloud (depth unprojected inside the SAM mask) moved into the reference object
                frame by a similarity fitted on the CAMERAS only (rotation from the per-view rotations, scale and
                shift from the camera centres), then compared to the GT mesh: mean nearest-neighbour distance in
                both directions, in % of the bounding-sphere radius (part radius = 100)
"""
import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image
from scipy.spatial import cKDTree

HERE = Path(__file__).parent
RC = HERE / "realcad"
OUT = HERE.parent / "out"
GL2CV = np.diag([1.0, -1.0, -1.0, 1.0])


def _rot24():
    import itertools
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3))
            for r, (c, s) in enumerate(zip(perm, signs)):
                R[r, c] = s
            if np.linalg.det(R) > 0:
                out.append(R)
    return out


R24_LIST = _rot24()


def rot_angle(R):
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def proj_rot(M):
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1
        R = U @ Vt
    return R


def axis_rot(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    i, j = [(1, 2), (0, 2), (0, 1)][axis]
    R = np.eye(3)
    R[i, i], R[i, j], R[j, i], R[j, j] = c, -s, s, c
    return R


def symmetry_group(G, tol=0.015):
    """Rotations (about the bbox centre, unit-sphere frame) that map the GT surface onto itself: the 24 axis-aligned
    ones plus turns about each axis in 10 deg steps (revolved parts). tol in units of the sphere radius."""
    P = G[np.random.default_rng(1).choice(len(G), 3000, replace=False)]
    tree = cKDTree(G)
    cands = list(R24_LIST)
    cands += [axis_rot(ax, d) for ax in range(3) for d in range(10, 360, 10)]
    return [R for R in cands if tree.query(P @ R.T)[0].mean() < tol]


def icp_similarity(P, G, R0, s0, t0, iters=30):
    """align P to G: x -> s R x + t, point-to-point ICP with scale, from an initial guess"""
    tree = cKDTree(G)
    R, s, t = R0, s0, t0
    for _ in range(iters):
        X = s * P @ R.T + t
        Y = G[tree.query(X)[1]]
        mx, my = P.mean(0), Y.mean(0)
        A, B = P - mx, Y - my
        U, S, Vt = np.linalg.svd(B.T @ A)
        D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ D @ Vt
        s = float((S * np.diag(D)).sum() / (A ** 2).sum())
        t = my - s * R @ mx
    X = s * P @ R.T + t
    d1 = tree.query(X)[0]
    d2 = cKDTree(X).query(G)[0]
    return 50 * float(d1.mean() + d2.mean()), 100 * float(d1.mean()), 100 * float(d2.mean())


def crop_resize(a, box, size, nearest=True):
    x0, y0, side = box
    im = Image.fromarray(a).crop((x0, y0, x0 + side, y0 + side))
    return np.asarray(im.resize((size, size), Image.NEAREST if nearest else Image.BILINEAR))


def score_part(pid, pred, crop, split="test50"):
    ref = json.loads((OUT / "pose_fit" / pid / "pose.json").read_text())
    ref_dep = np.load(OUT / "pose_fit" / pid / "depth.npz")
    views = [int(v) for v in pred["views"]]
    E = pred["extrinsics"].astype(np.float64)
    Kp = pred["intrinsics"].astype(np.float64)
    dep = pred["depth"].astype(np.float32)
    H, W = dep.shape[-2:]
    box, size = crop["box"], crop["size"]
    s_img = box[2] / W                                     # crop px -> photo px
    # reference cameras (object frame, OpenCV w2c)
    Rg, Cg = [], []
    for k in views:
        c2w = np.array(ref["views"][str(k)]["c2w"]) @ GL2CV
        Rg.append(c2w[:3, :3].T)
        Cg.append(c2w[:3, 3])
    Rp = [E[i, :, :3] for i in range(len(views))]
    Cp = [-E[i, :, :3].T @ E[i, :, 3] for i in range(len(views))]
    m = trimesh.load(RC / split / "meshes" / f"{pid}.stl")
    m.apply_translation(-np.array(ref["centre"]))
    m.apply_scale(ref["scale"])
    G, _ = trimesh.sample.sample_surface(m, 20000, seed=0)
    sym = symmetry_group(G)
    # 1) relative rotations, raw and modulo the part's own symmetries (a half-turn of a plate is not an error)
    pairs_ij = [(i, j) for i in range(len(views)) for j in range(i + 1, len(views))]
    errs = [rot_angle((Rp[i] @ Rp[j].T) @ (Rg[i] @ Rg[j].T).T) for i, j in pairs_ij]
    errs_sym = [min(rot_angle((Rp[i] @ Rp[j].T) @ (Rg[i] @ h @ Rg[j].T).T) for h in sym) for i, j in pairs_ij]
    # 2) focal
    f_pred = float(np.mean([(Kp[i, 0, 0] + Kp[i, 1, 1]) / 2 for i in range(len(views))]) * s_img)
    f_ref = ref["camera"]["focal_px"]
    # 3) depth up to one scale per part
    masks = {k: crop_resize((np.asarray(Image.open(RC / split / "images" / pid / "mask" / f"{k}.png").convert("L"))
                             > 127).astype(np.uint8), box, W) > 0 for k in views}
    dref = {k: crop_resize(ref_dep[str(k)].astype(np.float32), box, W) for k in views}
    ratios, pairs = [], []
    for i, k in enumerate(views):
        ok = masks[k] & (dref[k] > 0) & (dep[i] > 0)
        ratios.append(dref[k][ok] / dep[i][ok])
        pairs.append((dep[i][ok], dref[k][ok]))
    s_d = float(np.median(np.concatenate(ratios)))
    absrel = float(np.mean(np.concatenate([np.abs(s_d * p - g) / g for p, g in pairs])))
    # 4) point cloud in the object frame via a camera-only similarity
    R_al = proj_rot(sum(Rg[i].T @ Rp[i] for i in range(len(views))))   # object <- pred world
    chamfer = None
    if len(views) >= 2:
        A = np.array([R_al @ c for c in Cp])
        B = np.array(Cg)
        Ac, Bc = A - A.mean(0), B - B.mean(0)
        s_al = float((Ac * Bc).sum() / max((Ac * Ac).sum(), 1e-12))
        t_al = B.mean(0) - s_al * A.mean(0)
        pts = []
        vv, uu = np.mgrid[:H, :W]
        for i, k in enumerate(views):
            ok = masks[k] & (dep[i] > 0)
            ray = np.linalg.inv(Kp[i]) @ np.stack([uu[ok] + 0.5, vv[ok] + 0.5, np.ones(ok.sum())])
            Xc = ray * dep[i][ok]
            Xw = Rp[i].T @ (Xc - E[i, :, 3:4])
            pts.append((s_al * (R_al @ Xw)).T + t_al)
        P = np.concatenate(pts)
        rng = np.random.default_rng(0)
        if len(P) > 20000:
            P = P[rng.choice(len(P), 20000, replace=False)]
        d1 = cKDTree(G).query(P)[0]
        d2 = cKDTree(P).query(G)[0]
        chamfer = {"pred_to_gt_%": 100 * float(d1.mean()), "gt_to_pred_%": 100 * float(d2.mean()),
                   "mean_%": 50 * float(d1.mean() + d2.mean())}
        # shape only (up to rotation + scale): best ICP similarity from the camera alignment and 24 turned starts
        Ps = P[rng.choice(len(P), min(5000, len(P)), replace=False)]
        Gs = G[rng.choice(len(G), 8000, replace=False)]
        mu = Ps.mean(0)
        best = None
        for R24 in R24_LIST:
            R0 = R24 @ R_al
            t0 = -s_al * R0 @ mu                                        # centre the cloud, keep the camera scale
            r = icp_similarity(Ps, Gs, R0, s_al, t0, iters=25)
            if best is None or r[0] < best[0]:
                best = r
        chamfer["shape_icp_%"] = best[0]
    return {"id": pid, "views": views, "n_sym": len(sym),
            "rot_err_deg_median": float(np.median(errs)) if errs else None,
            "rot_err_sym_deg_median": float(np.median(errs_sym)) if errs_sym else None,
            "rot_errs": [round(e, 2) for e in errs], "rot_errs_sym": [round(e, 2) for e in errs_sym],
            "focal_pred_px": round(f_pred, 1), "focal_ref_px": f_ref,
            "focal_err_%": round(100 * (f_pred - f_ref) / f_ref, 2), "depth_absrel": round(absrel, 4),
            "chamfer": chamfer, "ref_mask_iou": ref.get("mean_mask_iou_filled", ref.get("mean_mask_iou"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--crops", default=str(OUT / "realcad_recon_in.crops.json"))
    a = ap.parse_args()
    crops = json.loads(Path(a.crops).read_text())
    z = zipfile.ZipFile(a.zip)
    names = {Path(n).stem: n for n in z.namelist() if n.startswith(f"{a.model}/") and n.endswith(".npz")}
    rows = []
    for pid in sorted(names):
        if not (OUT / "pose_fit" / pid / "pose.json").exists():
            continue
        pred = np.load(io.BytesIO(z.read(names[pid])))
        r = score_part(pid, pred, crops[pid])
        rows.append(r)
        c = r["chamfer"]
        print(f"{pid}  sym {r['n_sym']}  rot {r['rot_err_deg_median']} / sym {r['rot_err_sym_deg_median']}  focal {r['focal_err_%']:+.1f}%  absrel {r['depth_absrel']:.3f}"
              f"  chamfer cams {'-' if c is None else round(c['mean_%'], 2)}%  shape {'-' if c is None else round(c['shape_icp_%'], 2)}%", flush=True)
    od = OUT / "recon_eval"
    od.mkdir(exist_ok=True)
    (od / f"{a.model}_per_part.json").write_text(json.dumps(rows, indent=1))
    allrot = np.concatenate([r["rot_errs"] for r in rows if r["rot_errs"]])
    allsym = np.concatenate([r["rot_errs_sym"] for r in rows if r["rot_errs_sym"]])
    sh = [r["chamfer"]["shape_icp_%"] for r in rows if r["chamfer"]]
    ch = [r["chamfer"]["mean_%"] for r in rows if r["chamfer"]]
    fe = np.abs([r["focal_err_%"] for r in rows])
    summ = {"model": a.model, "parts": len(rows), "view_pairs": int(len(allrot)),
            "rot_err_deg_median": float(np.median(allrot)), "rot_err_deg_mean": float(np.mean(allrot)),
            "pairs_within_5deg_%": float(100 * np.mean(allrot < 5)), "pairs_within_10deg_%": float(100 * np.mean(allrot < 10)),
            "pairs_within_15deg_%": float(100 * np.mean(allrot < 15)),
            "rot_err_sym_deg_median": float(np.median(allsym)),
            "pairs_sym_within_5deg_%": float(100 * np.mean(allsym < 5)), "pairs_sym_within_10deg_%": float(100 * np.mean(allsym < 10)),
            "pairs_sym_within_15deg_%": float(100 * np.mean(allsym < 15)),
            "shape_icp_%_median": float(np.median(sh)), "shape_icp_%_mean": float(np.mean(sh)),
            "focal_abs_err_%_median": float(np.median(fe)),
            "depth_absrel_median": float(np.median([r["depth_absrel"] for r in rows])),
            "chamfer_mean_%_median": float(np.median(ch)), "chamfer_mean_%_mean": float(np.mean(ch))}
    (od / f"{a.model}_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
