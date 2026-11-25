"""Poster figure "what the checker sees": target view, cadrille's program, silhouette
residual and depth error for one Stage 1 part, in two views.

    uv run python poster/make_example_figure.py            # -> poster/figures/checker_example.png
    uv run python poster/make_example_figure.py --part 38675_6e07d74b_0004 --views top_back top_left

It first renders cadrille's starting program with a free dry run of refine.py
(--backend echo --rounds 0, no model calls) into runs/poster_example/, then composes the
panels from that run's renders/ and diff/ folders. Needs the Stage 1 targets and the
cadrille starting programs (data/generated/, see README).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import layout  # noqa: E402

COLUMNS = ["Target view\n(input)", "cadrille's\nprogram", "Silhouette\nresidual", "Depth\nerror"]


def ensure_run(part: str, targets: Path, init: Path, run: Path) -> Path:
    cand = run / "parts" / part / "init"
    if not (cand / "diff" / "report.json").exists():
        subprocess.run([sys.executable, str(ROOT / "refine.py"), str(targets / part),
                        "--init", str(init), "--arm", "geo", "--rounds", "0",
                        "--backend", "echo", "--out", str(run)], check=True, cwd=ROOT)
    return cand


def crop_box(images, pad=14, thresh=245):
    """Union bounding box of the non-white pixels of same-sized images."""
    mask = np.zeros(images[0].shape[:2], bool)
    for im in images:
        mask |= (im[..., :3] < thresh).any(axis=-1)
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    return (max(ys.min() - pad, 0), min(ys.max() + pad, h), max(xs.min() - pad, 0),
            min(xs.max() + pad, w))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--part", default="61899_93eee6e5_0000")
    ap.add_argument("--views", nargs="+", default=["top_front", "top_right"])
    ap.add_argument("--targets", type=Path, default=ROOT / "data/generated/targets/fusion360")
    ap.add_argument("--init", type=Path, default=ROOT / "data/generated/init/cadrille_rl")
    ap.add_argument("--run", type=Path, default=ROOT / "runs/poster_example")
    ap.add_argument("--out", type=Path, default=ROOT / "poster/figures/checker_example.png")
    args = ap.parse_args(argv)

    target = args.targets / args.part
    cand = ensure_run(args.part, args.targets, args.init, args.run)
    report = json.loads(layout.diff(cand, args.views[0], "_overlay").parent
                        .joinpath("report.json").read_text())
    iou3d = None
    log = args.run / "parts" / args.part / "geo" / "log.jsonl"
    if log.exists():
        iou3d = json.loads(log.read_text().splitlines()[0]).get("iou3d")

    fig, axes = plt.subplots(len(args.views), 4, figsize=(12, 3.3 * len(args.views) + 2.4),
                             squeeze=False)
    for r, v in enumerate(args.views):
        ims = [np.asarray(Image.open(p).convert("RGB")) for p in (
            layout.render(target, v), layout.render(cand, v),
            layout.diff(cand, v, "_overlay"), layout.diff(cand, v, "_depth_err"))]
        y0, y1, x0, x1 = crop_box(ims)
        for c, im in enumerate(ims):
            ax = axes[r, c]
            ax.imshow(im[y0:y1, x0:x1])
            ax.set_xticks([]), ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color("#d0d0d0")
            if r == 0:
                ax.set_title(COLUMNS[c], fontsize=22, pad=10)
        m = report["views"][v]
        axes[r, 0].set_ylabel(f"{v}\nIoU {m['iou']:.2f}", fontsize=19)

    handles = [Patch(color="#c8c8c8", label="both"),          # compare.py BOTH / MISSING / EXTRA
               Patch(color="#d72626", label="missing"),
               Patch(color="#2662d7", label="extra")]
    fig.legend(handles=handles, loc="center", ncol=3, fontsize=19, frameon=False,
               bbox_to_anchor=(0.5, 0.075), title="silhouette:", title_fontsize=19,
               alignment="left")
    fig.text(0.5, 0.022, "depth: pale = right depth, dark red = wrong depth", fontsize=19,
             ha="center", va="center")
    if iou3d is not None:
        fig.suptitle(f"cadrille's program: 3D IoU {iou3d:.2f} (hidden from the agent)",
                     fontsize=21, y=0.99)
    fig.tight_layout(rect=(0, 0.12, 1, 0.95))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=250, facecolor="white")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
