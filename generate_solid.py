"""Run a CadQuery program, check the solid it makes, export it and render it.

The program is a .py file that assigns its final shape to `result`
(a cq.Workplane or cq.Shape).

    uv run python generate_solid.py examples/flange.py --out out/flange
"""
import argparse
import json
import runpy
import sys
import traceback
from pathlib import Path

import cadquery as cq
import numpy as np
from PIL import Image

from cq_render import CQRenderer, to_trimesh
from rig import load_rig, normalize, render_rig


def load_solid(program: Path) -> cq.Shape:
    """Execute the program and return its `result` as a single cq.Shape."""
    ns = runpy.run_path(str(program), run_name="__cad__")
    if "result" not in ns:
        raise ValueError(f"{program} does not define `result`")
    res = ns["result"]
    if isinstance(res, cq.Workplane):
        vals = [v for v in res.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValueError("`result` Workplane contains no shapes")
        res = vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if not isinstance(res, cq.Shape):
        raise TypeError(f"`result` is {type(res).__name__}, expected Workplane or Shape")
    return res


def check_solid(shape: cq.Shape) -> dict:
    """Basic validity stats; raises if the shape is not a usable solid."""
    solids = shape.Solids()
    bb = shape.BoundingBox()
    info = {
        "valid": shape.isValid(),
        "n_solids": len(solids),
        "n_faces": len(shape.Faces()),
        "volume": shape.Volume(),
        "bbox_min": [bb.xmin, bb.ymin, bb.zmin],
        "bbox_max": [bb.xmax, bb.ymax, bb.zmax],
    }
    if not solids:
        raise ValueError("shape contains no solids")
    if info["volume"] <= 0:
        raise ValueError(f"non-positive volume {info['volume']}")
    return info


def generate(program: Path, out: Path, rig: dict) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    shape = load_solid(program)
    info = check_solid(shape)
    cq.exporters.export(shape, str(out / "solid.step"))
    cq.exporters.export(shape, str(out / "solid.stl"))

    mesh, center, scale = normalize(to_trimesh(shape))
    with CQRenderer(rig["width"], rig["height"]) as r:
        views = render_rig(r, mesh, rig)
    for name, (rgb, depth, mask) in views.items():
        Image.fromarray(rgb).save(out / f"{name}.png")
        Image.fromarray((mask * 255).astype(np.uint8)).save(out / f"{name}_mask.png")
    np.savez_compressed(out / "depth.npz", **{n: v[1] for n, v in views.items()})
    # x_normalised = (x - center) * scale ; depth is in normalised units
    info["normalization"] = {"center": center.tolist(), "scale": float(scale)}
    info["views"] = list(views)
    (out / "info.json").write_text(json.dumps(info, indent=2))
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("program", type=Path, help="CadQuery .py file defining `result`")
    ap.add_argument("--out", type=Path, default=None, help="default: out/<program name>")
    ap.add_argument("--rig", type=Path, default=None, help="camera rig json (default: rig.json)")
    args = ap.parse_args()
    out = args.out or Path("out") / args.program.stem
    try:
        info = generate(args.program, out, load_rig(args.rig) if args.rig else load_rig())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    print(json.dumps(info, indent=2))
    print(f"wrote solid.step, solid.stl, depth.npz and {len(info['views'])} views to {out}/")


if __name__ == "__main__":
    main()
