"""Offline 3D evaluation: how close is a candidate solid to the hidden true shape?

Only the experiment uses this, to score runs afterwards. The agent and the acceptance
rules never see it (at test time there is no 3D model).

    uv run python eval3d.py out/targets/fusion360/<part> out/refine/<part>/geo/round_02

The target dir holds the hidden shape as solid.step (+ solid.stl), from generate_solid.py,
or as gt.stl only (mesh datasets such as Fusion360). The candidate is a generate_solid.py
output rendered with --like <target>, so both are in the same frame.

Fixed-frame metrics (strict: size and position errors count; distances in the target's
normalised frame, i.e. units of its bounding-sphere radius):
  iou3d          volume IoU (exact CAD booleans for STEP targets, mesh booleans otherwise)
  iogt           |cand AND gt| / |gt|, intersection over ground truth (CADCodeVerify)
  chamfer_x1000  symmetric mean nearest-surface distance x1000
  hausdorff      max nearest-surface distance (CADCodeVerify)
  f1             F-score of surface samples at 1% of the bounding diameter (GATOR)
  normal_consistency  mean |cos| between normals of nearest surface samples (GATOR)
cadrille protocol (comparable with cadrille's tables; each mesh bbox-normalised to the
unit cube on its own, so scale errors are forgiven):
  iou3d_cad, cd_cad  (cd = mean squared distances, x1000, as cadrille's evaluate.py)

`failed()` gives the values for a candidate that does not build: overlap scores 0
(CADCodeVerify's convention), distances None (summaries report them over valid ones and
give the compile rate next to them).
"""
import argparse
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree

N_POINTS = 8192          # cadrille protocol
N_SURFACE = 30000        # fixed-frame surface metrics; 8192 is too sparse for F1 at 1%
                         # (GT vs itself scores F1 ~0.9-0.95 with 8192, 1.0 with 30000)
F1_FRACTION = 0.01


def load_step(path: Path) -> cq.Shape:
    return cq.importers.importStep(str(path)).val()


def iou3d(a: cq.Shape, b: cq.Shape):
    """Volume IoU via OCC booleans; None if the boolean fails."""
    try:
        inter = a.intersect(b).Volume()
    except Exception:
        return None
    va, vb = a.Volume(), b.Volume()
    union = va + vb - inter
    return float(inter / union) if union > 0 else None


def mesh_overlap(gt: trimesh.Trimesh, cand: trimesh.Trimesh):
    """(intersection volume, gt volume, candidate volume) by mesh booleans (manifold),
    per connected piece as cadrille does; None if the boolean fails."""
    try:
        inter = 0.0
        for a in gt.split(only_watertight=False):
            for b in cand.split(only_watertight=False):
                x = a.intersection(b, engine="manifold")
                inter += x.volume if x is not None and len(x.faces) else 0.0
        vg = sum(abs(m.volume) for m in gt.split(only_watertight=False))
        vc = sum(abs(m.volume) for m in cand.split(only_watertight=False))
        return float(inter), float(vg), float(vc)
    except Exception:
        return None


def _samples(mesh, n, seed):
    pts, face = trimesh.sample.sample_surface(mesh, n, seed=seed)
    return pts, mesh.face_normals[face]


def surface_metrics(gt, cand, scale: float, n=N_SURFACE, seed=0):
    """Chamfer x1000, Hausdorff, F1 and normal consistency in units of 1/scale."""
    pg, ng = _samples(gt, n, seed)
    pc, nc = _samples(cand, n, seed + 1)
    pg, pc = pg * scale, pc * scale
    d_gc, i_gc = cKDTree(pc).query(pg)
    d_cg, i_cg = cKDTree(pg).query(pc)
    diam = float(np.linalg.norm(gt.extents)) * scale
    tau = F1_FRACTION * diam
    prec, rec = float((d_cg < tau).mean()), float((d_gc < tau).mean())
    nc_val = 0.5 * (np.abs((ng * nc[i_gc]).sum(1)).mean() + np.abs((nc * ng[i_cg]).sum(1)).mean())
    return {"chamfer_x1000": float((d_gc.mean() + d_cg.mean()) / 2 * 1000),
            "hausdorff": float(max(d_gc.max(), d_cg.max())),
            "f1": 2 * prec * rec / (prec + rec) if prec + rec > 0 else 0.0,
            "normal_consistency": float(nc_val)}


def unit_cube(mesh):
    """cadrille's normalisation: bbox centre to 0.5, longest side 1."""
    m = mesh.copy()
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    m.apply_scale(1.0 / m.extents.max())
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def cadrille_protocol(gt, cand, n=N_POINTS, seed=0):
    g, c = unit_cube(gt), unit_cube(cand)
    a = trimesh.sample.sample_surface(g, n, seed=seed)[0]
    b = trimesh.sample.sample_surface(c, n, seed=seed + 1)[0]
    d1, d2 = cKDTree(a).query(b)[0], cKDTree(b).query(a)[0]
    ov = mesh_overlap(g, c)
    iou = None if ov is None else ov[0] / (ov[1] + ov[2] - ov[0])
    return {"iou3d_cad": iou, "cd_cad": float((np.mean(d1 ** 2) + np.mean(d2 ** 2)) * 1000)}


def evaluate(target_dir: Path, cand_dir: Path) -> dict:
    target_dir, cand_dir = Path(target_dir), Path(cand_dir)
    scale = json.loads((target_dir / "info.json").read_text())["normalization"]["scale"]
    gt_mesh_path = target_dir / "gt.stl"
    if not gt_mesh_path.exists():
        gt_mesh_path = target_dir / "solid.stl"
    mt = trimesh.load(gt_mesh_path, force="mesh")
    mc = trimesh.load(cand_dir / "solid.stl", force="mesh")
    out = {}
    if (target_dir / "solid.step").exists():          # exact CAD booleans
        t, c = load_step(target_dir / "solid.step"), load_step(cand_dir / "solid.step")
        out["iou3d"] = iou3d(t, c)
        try:
            out["iogt"] = float(t.intersect(c).Volume() / t.Volume())
        except Exception:
            out["iogt"] = None
    else:                                             # mesh ground truth
        ov = mesh_overlap(mt, mc)
        if ov is None:
            out.update(iou3d=None, iogt=None)
        else:
            inter, vg, vc = ov
            out["iou3d"] = inter / (vg + vc - inter) if vg + vc - inter > 0 else None
            out["iogt"] = inter / vg if vg > 0 else None
    out.update(surface_metrics(mt, mc, scale))
    out.update(cadrille_protocol(mt, mc))
    return out


def properties(mesh: trimesh.Trimesh) -> dict:
    """Geometric properties of a solid, as CADCodeVerify's geometric-solver feedback lists
    them. Uses the true shape when applied to the GT -> only for the gsolver* upper bound."""
    pieces = mesh.split(only_watertight=False)
    ext = mesh.extents
    return {"size_x": float(ext[0]), "size_y": float(ext[1]), "size_z": float(ext[2]),
            "volume": float(abs(mesh.volume)), "surface_area": float(mesh.area),
            "pieces": int(len(pieces)),
            # genus per piece from Euler characteristic: through-holes/handles
            "through_holes": int(sum(max(0, round((2 - p.euler_number) / 2)) for p in pieces)),
            "centroid_x": float(mesh.centroid[0]), "centroid_y": float(mesh.centroid[1]),
            "centroid_z": float(mesh.centroid[2])}


def failed() -> dict:
    """Scores for a program that never built: overlap 0, distances undefined."""
    return {"iou3d": 0.0, "iogt": 0.0, "chamfer_x1000": None, "hausdorff": None,
            "f1": 0.0, "normal_consistency": 0.0, "iou3d_cad": 0.0, "cd_cad": None}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", type=Path)
    ap.add_argument("candidate", type=Path)
    args = ap.parse_args()
    print(json.dumps(evaluate(args.target, args.candidate), indent=2))


if __name__ == "__main__":
    main()
