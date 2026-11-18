"""How much to trust each target view: cross-view consistency of the observations.

Every view's depth map is back-projected to 3D and checked against every other view
(a space-carving test): a point seen by view v must, in view u, land on u's silhouette
and must not lie in front of u's visible surface (it would have been seen there). Points
hidden behind u's surface are fine (occlusion). For each pair of views

    r(v, u) = 1/2 * (share of v's points that u rejects + share of u's points that v rejects)

and a view's consistency is c_v = 1 - median_u r(v, u). The median makes one bad view
unable to drag the good ones down, while the bad view itself disagrees with all of them.
The weight is c_v mapped to [0, 1]:  w_v = clip((c_v - C_MIN) / (C_FULL - C_MIN), 0, 1).

Uses only the target's masks, depth maps and the calibrated rig -- never the 3D model.
On clean renders every weight is ~1 (the Stage 1 sanity check); with corrupted masks or
depth (Stage 2) the views that disagree with the rest get down-weighted.

    uv run python view_weights.py data/generated/targets/fusion360/<part>
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

import layout
from rig import load_rig

# clean renders give c = 1.000 exactly; a 25 px shift or 0.15 depth bias of one view gives
# c ~ 0.65-0.92 for that view only (measured on Fusion360 parts), so map 0.6..0.98 -> 0..1
C_MIN, C_FULL = 0.6, 0.98
DEPTH_TOL = 0.03       # normalised units (unit bounding sphere)
MAX_POINTS = 4000      # per view, subsampled for speed
CACHE = "view_weights.json"


# ------------------------------------------------------------------ geometry
def backproject(depth: np.ndarray, cam: dict, K) -> np.ndarray:
    """Foreground pixels of one depth map -> Nx3 points in the normalised world frame."""
    K = np.asarray(K)
    v, u = np.nonzero(depth > 0)
    z = depth[v, u].astype(np.float64)
    x = (u + 0.5 - K[0, 2]) / K[0, 0] * z
    y = -(v + 0.5 - K[1, 2]) / K[1, 1] * z          # image down -> camera -y (OpenGL)
    P = np.asarray(cam["pose_c2w"], np.float64)
    with np.errstate(all="ignore"):  # spurious matmul warnings from macOS Accelerate
        return np.stack([x, y, -z], 1) @ P[:3, :3].T + P[:3, 3]


def project(pts: np.ndarray, cam: dict, K):
    """Nx3 world points -> (row, col, z) pixel coords and depth along the view axis."""
    K = np.asarray(K)
    P = np.asarray(cam["pose_c2w"], np.float64)
    with np.errstate(all="ignore"):
        pc = (pts - P[:3, 3]) @ P[:3, :3]             # world -> camera (R^T (p - t))
    z = -pc[:, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        col = pc[:, 0] / z * K[0, 0] + K[0, 2] - 0.5
        row = K[1, 2] - pc[:, 1] / z * K[1, 1] - 0.5
    return np.rint(row).astype(int), np.rint(col).astype(int), z


def _rejected(pts, depth_u, near_u, cam_u, K):
    """Share of `pts` that view u contradicts (None if none of them fall in u's image)."""
    h, w = depth_u.shape
    row, col, z = project(pts, cam_u, K)
    inside = (z > 0) & (row >= 0) & (row < h) & (col >= 0) & (col < w)
    if not inside.any():
        return None
    row, col, z = row[inside], col[inside], z[inside]
    d = near_u[row, col]          # nearest surface within 1 px; inf = off the silhouette
    ok = np.isfinite(d) & (z >= d - DEPTH_TOL)
    return float(1.0 - ok.mean())


def measure_bbox(target_dir: Path, rig: dict):
    """Bounding box (target units) of the target from its depth maps and the calibrated
    cameras: back-project every foreground pixel of every view. Uses no 3D model."""
    info = json.loads(layout.info(target_dir).read_text())
    center = np.array(info["normalization"]["center"])
    scale = info["normalization"]["scale"]
    depth = np.load(layout.depth(target_dir))
    pts = np.concatenate([backproject(depth[c["name"]], c, rig["K"])
                          for c in rig["cameras"] if c["name"] in depth.files])
    pts = pts / scale + center                              # normalised -> target units
    return pts.min(0), pts.max(0)


# ------------------------------------------------------------------ weights
def consistency(depths: dict, rig: dict, seed=0) -> dict:
    """{view: depth map} -> {view: c_v in [0, 1]}."""
    rng = np.random.default_rng(seed)
    cams = {c["name"]: c for c in rig["cameras"] if c["name"] in depths}
    names = list(cams)
    pts, near = {}, {}
    for n in names:
        p = backproject(depths[n], cams[n], rig["K"])
        if len(p) > MAX_POINTS:
            p = p[rng.choice(len(p), MAX_POINTS, replace=False)]
        pts[n] = p
        d = np.where(depths[n] > 0, depths[n].astype(np.float64), np.inf)
        near[n] = ndimage.minimum_filter(d, size=3, mode="constant", cval=np.inf)
    rej = {}
    for v in names:
        for u in names:
            if u != v and len(pts[v]):
                rej[v, u] = _rejected(pts[v], depths[u], near[u], cams[u], rig["K"])
    out = {}
    for v in names:
        pair = []
        for u in names:
            if u == v:
                continue
            a, b = rej.get((v, u)), rej.get((u, v))
            vals = [x for x in (a, b) if x is not None]
            if vals:
                pair.append(float(np.mean(vals)))
        out[v] = 1.0 - float(np.median(pair)) if pair else 0.0
    return out


def to_weights(cons: dict) -> dict:
    return {v: float(np.clip((c - C_MIN) / (C_FULL - C_MIN), 0.0, 1.0)) for v, c in cons.items()}


def view_weights(target_dir: Path, rig: dict | None = None, cache=True) -> dict:
    """Per-view weights of a target dir, cached in <target>/internal/view_weights.json."""
    target_dir = Path(target_dir)
    f = layout.internal(target_dir, CACHE)
    if cache and f.exists():
        return json.loads(f.read_text())["weights"]
    rig = rig or load_rig()
    depth = np.load(layout.depth(target_dir))
    cons = consistency({k: depth[k] for k in depth.files}, rig)
    w = to_weights(cons)
    if cache:
        f.parent.mkdir(exist_ok=True)
        f.write_text(json.dumps({"weights": w, "consistency": cons,
                                 "c_min": C_MIN, "c_full": C_FULL,
                                 "depth_tol": DEPTH_TOL}, indent=2) + "\n")
    return w


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", type=Path)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()
    w = view_weights(args.target, cache=not args.no_cache)
    for v, x in w.items():
        print(f"{v:8s} {x:.3f}")


if __name__ == "__main__":
    main()
