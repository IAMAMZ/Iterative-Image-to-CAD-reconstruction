"""Build refine.py targets from the Fusion360 ground-truth meshes.

    uv run python data/fusion360_targets.py                       # Stage 1 split
    uv run python data/fusion360_targets.py --split data/splits/fusion360_test.txt --limit 5

reads   cadrille/results/fusion360_test_gt/<part>.stl   (committed; unit cube [0,1]^3)
writes  out/targets/fusion360/<part>/  laid out like a generate_solid.py output:
          <view>.png, <view>_mask.png, <view>_depth.png, depth.npz, info.json
        plus gt.stl (the hidden true shape, for offline scoring only; the agent never reads it)

Frame: cadrille writes its programs in a canonical frame centred on the bounding box with
the longest side ~200 (coordinates roughly -100..100). The GT meshes are the same shapes in
the unit cube, so  x_target = (x_gt - 0.5) * 200  puts target and cadrille program in one
frame. All lengths the agent sees are in these "units", not mm.
"""
import argparse
import json
import sys
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_solid import render_mesh  # noqa: E402
from rig import load_rig  # noqa: E402

GT_DIR = ROOT / "cadrille" / "results" / "fusion360_test_gt"
DEFAULT_SPLIT = ROOT / "data" / "splits" / "fusion360_stage1.txt"
DEFAULT_OUT = ROOT / "out" / "targets" / "fusion360"
CADRILLE_SIDE = 200.0


def to_target_frame(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Unit-cube GT mesh -> cadrille's frame (bbox-centred, longest side 200)."""
    m = mesh.copy()
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    m.apply_scale(CADRILLE_SIDE / m.extents.max())
    return m


def build_target(part: str, out_root: Path, rig: dict, gt_dir: Path = GT_DIR) -> dict:
    mesh = to_target_frame(trimesh.load_mesh(gt_dir / f"{part}.stl", force="mesh"))
    out = out_root / part
    out.mkdir(parents=True, exist_ok=True)
    mesh.export(out / "gt.stl")
    info = {"source": "fusion360", "part": part, "units": "cadrille units (longest side 200)",
            "gt_watertight": bool(mesh.is_watertight), "n_faces_gt": int(len(mesh.faces)),
            "n_vertices_gt": int(len(mesh.vertices))}
    return render_mesh(mesh, out, rig, None, info)


def read_split(path: Path):
    return [l.strip() for l in path.read_text().split() if l.strip() and not l.startswith("#")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="rebuild targets that already exist")
    args = ap.parse_args()
    rig = load_rig()
    parts = read_split(args.split)[:args.limit]
    done = failed = 0
    for i, p in enumerate(parts, 1):
        if (args.out / p / "info.json").exists() and not args.force:
            continue
        try:
            build_target(p, args.out, rig)
            done += 1
        except Exception as e:  # keep going; report at the end
            failed += 1
            print(f"{p}: {type(e).__name__}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"{i}/{len(parts)}", flush=True)
    print(f"built {done} targets in {args.out} ({failed} failed, "
          f"{len(parts) - done - failed} already there)")


if __name__ == "__main__":
    main()
