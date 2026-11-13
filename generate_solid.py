"""Run a CadQuery program, check the solid it makes, export it and render it.

The program is a .py file that assigns its final shape to `result`
(a cq.Workplane or cq.Shape).

    uv run python generate_solid.py examples/flange.py --out out/flange

Every CadQuery operation is checked as it runs (see op_checker.py) and logged to
<out>/ops_log.jsonl, also when the run fails. Exit code 1 = the program or one of its
operations was illegal; the log says which step, which line, why, and a hint.
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
from op_checker import IllegalOperation, OpTrace, format_step
from rig import load_rig, normalize, render_rig

# files a run writes; removed first so a failed run never leaves stale results behind
OUTPUTS = ("info.json", "solid.step", "solid.stl", "depth.npz", "ops_log.jsonl")


class InvalidSolid(ValueError):
    """The program ran, but what it built is not a usable solid."""

    def __init__(self, message, hint=None):
        super().__init__(message)
        self.hint = hint


def load_solid(program: Path, trace: OpTrace | None = None) -> cq.Shape:
    """Execute the program and return its `result` as a single cq.Shape.
    With a trace, every Workplane operation is checked and logged while it runs."""
    if trace is None:
        ns = runpy.run_path(str(program), run_name="__cad__")
    else:
        with trace:
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
    """Basic validity stats; raises InvalidSolid if the shape is not a usable solid."""
    solids = shape.Solids()
    if not solids:  # check first: an empty result has no bounding box either
        raise InvalidSolid("shape contains no solids",
                           hint="`result` must be a 3D solid, not a face, wire or sketch; "
                                "extrude/revolve it, and don't end on a selector like .faces()")
    if not shape.isValid():
        raise InvalidSolid("shape is not valid (e.g. self-intersecting geometry)",
                           hint="built with the low-level API? check the shapes it combines")
    bb = shape.BoundingBox()
    volume = shape.Volume()
    # "positive" relative to the part's size, so float noise like 1e-14 doesn't count
    if volume <= 1e-9 * bb.DiagonalLength ** 3:
        raise InvalidSolid(f"shape has (near) zero volume: {volume:g}",
                           hint="the part is flat or degenerate")
    return {
        "valid": True,
        "n_solids": len(solids),
        "n_faces": len(shape.Faces()),
        "volume": volume,
        "bbox_min": [bb.xmin, bb.ymin, bb.zmin],
        "bbox_max": [bb.xmax, bb.ymax, bb.zmax],
    }


def depth_preview(depth: np.ndarray) -> np.ndarray:
    """Greyscale picture of a depth map for viewing only: near = white, far = dark,
    background = black. Stretched per image, so don't use it for measurements."""
    img = np.zeros(depth.shape, dtype=np.uint8)
    fg = depth > 0
    if fg.any():
        lo, hi = depth[fg].min(), depth[fg].max()
        t = (hi - depth[fg]) / max(hi - lo, 1e-9)  # 1 at nearest, 0 at farthest
        img[fg] = (55 + 200 * t).astype(np.uint8)   # keep far surfaces visible over black
    return img


def generate(program: Path, out: Path, rig: dict, normalization: dict | None = None,
             center_at=None) -> dict:
    """normalization: {"center", "scale"} to reuse (e.g. a target's info.json entry);
    default fits this part to the unit sphere.
    center_at: (x, y, z) in mm; move the solid so its bounding-box centre lands there
    (forgives a guess that has the right shape but sits in the wrong place)."""
    out.mkdir(parents=True, exist_ok=True)
    views_png = [f"{c['name']}{sfx}.png" for c in rig["cameras"] for sfx in ("", "_mask", "_depth")]
    for f in [*OUTPUTS, *views_png]:
        (out / f).unlink(missing_ok=True)
    trace = OpTrace(program)
    try:
        shape = load_solid(program, trace)
        info = check_solid(shape)
        if center_at is not None:
            c = (np.array(info["bbox_min"]) + np.array(info["bbox_max"])) / 2
            shift = np.asarray(center_at, float) - c
            shape = shape.translate(cq.Vector(*shift))
            info = check_solid(shape)
            info["translated_by"] = shift.tolist()
        trace.record_result(shape)
    except IllegalOperation:
        raise  # already logged by the trace, at the operation that caused it
    except Exception as e:
        trace.record_failure(e, op="check_result" if isinstance(e, InvalidSolid) else "program")
        raise
    finally:
        trace.write_jsonl(out / "ops_log.jsonl")
    info["ops"] = {"n_steps": len(trace.steps),
                   "warnings": [format_step(s) for s in trace.warnings]}
    cq.exporters.export(shape, str(out / "solid.step"))
    cq.exporters.export(shape, str(out / "solid.stl"))

    norm = normalization or {}
    mesh, center, scale = normalize(to_trimesh(shape), norm.get("center"), norm.get("scale"))
    with CQRenderer(rig["width"], rig["height"]) as r:
        views = render_rig(r, mesh, rig)
    for name, (rgb, depth, mask) in views.items():
        Image.fromarray(rgb).save(out / f"{name}.png")
        Image.fromarray((mask * 255).astype(np.uint8)).save(out / f"{name}_mask.png")
        Image.fromarray(depth_preview(depth)).save(out / f"{name}_depth.png")
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
    ap.add_argument("--like", type=Path, default=None,
                    help="output dir of a target part: render in the target's frame "
                         "(same centre and scale) so the two can be compared with compare.py")
    ap.add_argument("--center-at", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"),
                    help="move the solid so its bounding-box centre is here (mm)")
    ap.add_argument("--traceback", action="store_true", help="also print the Python traceback")
    args = ap.parse_args()
    out = args.out or Path("out") / args.program.stem
    norm = json.loads((args.like / "info.json").read_text())["normalization"] if args.like else None
    try:
        info = generate(args.program, out, load_rig(args.rig) if args.rig else load_rig(), norm,
                        args.center_at)
    except Exception as e:
        if args.traceback:
            traceback.print_exc()
        log = out / "ops_log.jsonl"
        steps = [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []
        for st in steps:
            if st["status"] != "ok":
                print(format_step(st), file=sys.stderr)
        if not any(st["status"] == "error" for st in steps):
            print(f"[ERROR  ] {type(e).__name__}: {e}", file=sys.stderr)
        print(f"FAILED, see {log}", file=sys.stderr)
        sys.exit(1)
    for w in info["ops"]["warnings"]:
        print(w)
    print(json.dumps({k: v for k, v in info.items() if k != "ops"}, indent=2))
    print(f"wrote solid.step, solid.stl, depth.npz and {len(info['views'])} views to {out}/")


if __name__ == "__main__":
    main()
