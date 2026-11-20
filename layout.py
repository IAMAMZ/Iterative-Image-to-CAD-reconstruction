"""Where files live inside a rendered-solid folder (a target, or a candidate program).

    <dir>/
      program.py            the CadQuery program (candidates)
      solid.stl  solid.step the built shape (gt.stl for mesh-only targets)
      renders/              <view>.png, <view>_mask.png, <view>_depth.png  (8 rig cameras)
      diff/                 vs the target: <view>_overlay.png, <view>_depth_err.png,
                            summary.png, report.json  (candidates)
      internal/             info.json, depth.npz, ops_log.jsonl (machine-readable)

Readers fall back to the older flat layout (everything at the top of <dir>), so archived
runs and targets built before this layout still load.
"""
from pathlib import Path

RENDERS, DIFF, INTERNAL = "renders", "diff", "internal"
INTERNAL_FILES = ("info.json", "depth.npz", "ops_log.jsonl")


def _pick(d: Path, sub: str, name: str) -> Path:
    new, old = Path(d) / sub / name, Path(d) / name
    return old if not new.exists() and old.exists() else new


def render(d: Path, view: str, kind: str = "") -> Path:
    """kind: "" (shaded), "_mask" or "_depth"."""
    return _pick(d, RENDERS, f"{view}{kind}.png")


def internal(d: Path, name: str) -> Path:
    return _pick(d, INTERNAL, name)


def info(d: Path) -> Path:
    return internal(d, "info.json")


def depth(d: Path) -> Path:
    return internal(d, "depth.npz")


def ops_log(d: Path) -> Path:
    return internal(d, "ops_log.jsonl")


def diff_dir(d: Path) -> Path:
    d = Path(d)
    return d / "compare" if not (d / DIFF).exists() and (d / "compare").exists() else d / DIFF


def diff(d: Path, view: str, kind: str) -> Path:
    """kind: "_overlay" or "_depth_err"."""
    return diff_dir(d) / f"{view}{kind}.png"


def is_rendered(d: Path) -> bool:
    return depth(d).exists() and info(d).exists()
