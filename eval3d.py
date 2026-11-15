"""Offline 3D evaluation: how close is a candidate solid to the hidden true solid?

Only the experiment uses this, to score runs afterwards. The agent and the
acceptance rules never see it (at test time there is no 3D model).

    uv run python eval3d.py out/pilot/bracket_000 out/refine/.../round_02

Both dirs are generate_solid.py outputs in the same mm frame (the candidate was
rendered with --like <target>). Measures
  * iou3d    volume IoU from exact CAD booleans (1 = identical solids)
  * chamfer  symmetric mean nearest-surface distance, in the target's normalised
             frame (unit bounding sphere), x1000 like cadrille reports it
"""
import argparse
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import cKDTree


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


def chamfer(mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh, scale: float, n=8192, seed=0):
    """Symmetric mean nearest-point distance between surface samples, in units of
    `scale` (the target's mm -> unit-sphere factor), x1000."""
    pa = trimesh.sample.sample_surface(mesh_a, n, seed=seed)[0] * scale
    pb = trimesh.sample.sample_surface(mesh_b, n, seed=seed)[0] * scale
    d_ab = cKDTree(pb).query(pa)[0]
    d_ba = cKDTree(pa).query(pb)[0]
    return float((d_ab.mean() + d_ba.mean()) / 2 * 1000)


def evaluate(target_dir: Path, cand_dir: Path) -> dict:
    scale = json.loads((target_dir / "info.json").read_text())["normalization"]["scale"]
    t, c = load_step(target_dir / "solid.step"), load_step(cand_dir / "solid.step")
    mt = trimesh.load(target_dir / "solid.stl", force="mesh")
    mc = trimesh.load(cand_dir / "solid.stl", force="mesh")
    return {"iou3d": iou3d(t, c), "chamfer_x1000": chamfer(mt, mc, scale)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", type=Path)
    ap.add_argument("candidate", type=Path)
    args = ap.parse_args()
    print(json.dumps(evaluate(args.target, args.candidate), indent=2))


if __name__ == "__main__":
    main()
