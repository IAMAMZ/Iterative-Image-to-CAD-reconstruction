"""Rebuild ground-truth solids for the RealCAD (printed + photographed) parts.

usage: python build_realcad_gt.py
reads   data/realcad/ids.txt, data/cad_json_realcad/ (local only)
writes  data/meshes_hidden/realcad/<part>.{step,stl}  canonical frame, original units (git-ignored)
        data/realcad/gt_manifest.json  built / failed / missing-json lists
No poses are applied: the real photos' camera and object poses are unknown.
"""
import json
from pathlib import Path

import cadquery as cq

from cad_build import build_shape
from render_views import to_mesh

HERE = Path(__file__).parent
SRC = HERE / "cad_json_realcad" / "cad_json"
OUT = HERE / "meshes_hidden" / "realcad"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = [l.strip() for l in open(HERE / "realcad" / "ids.txt") if l.strip()]
    built, failed, missing = {}, {}, []
    for pid in ids:
        src = SRC / f"{pid}.json"
        if not src.exists():
            missing.append(pid)
            continue
        name = pid.split("/")[1]
        try:
            shape = build_shape(src)
            mesh = to_mesh(shape)
            cq.exporters.export(cq.Workplane(obj=shape), str(OUT / f"{name}.step"))
            mesh.export(OUT / f"{name}.stl")
            built[pid] = {"n_triangles": int(len(mesh.faces)), "watertight": bool(mesh.is_watertight),
                          "volume": float(shape.Volume())}
        except Exception as e:  # report, never silently drop
            failed[pid] = f"{type(e).__name__}: {e}"
    json.dump({"built": built, "failed": failed, "missing_json": missing},
              open(HERE / "realcad" / "gt_manifest.json", "w"), indent=2)
    print(f"built {len(built)}, failed {len(failed)}, missing json {len(missing)}")
    for k, v in failed.items():
        print("  FAILED", k, v)


if __name__ == "__main__":
    main()
