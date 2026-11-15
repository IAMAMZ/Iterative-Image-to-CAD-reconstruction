"""Figures for the report/poster from a refine.py output dir.

    uv run python figures.py out/refine            # -> out/refine/figures/*.png

  iou_by_round.png    mean hidden 3D IoU of the kept program after each round, per arm
  iou_vs_time.png     the same against cumulative wall time (GATOR Fig. 6 style)
  edit_outcomes.png   kept / dropped edits split by what they did to the hidden shape
  montage_<part>.png  target | first program | final program of each arm (iso view),
                      with the final silhouette residual underneath
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from summarize_runs import load, outcome  # noqa: E402

COLORS = {"premise": "#8c8c8c", "vlm": "#2a6fdb", "geo": "#e07b00", "hybrid": "#1a9e5a",
          "oracle": "#7a3fb8", "gsolver": "#c23b3b"}


def kept_trajectories(rows):
    """{arm: {part: [iou3d of the kept program after round 0, 1, ...]}} and wall times."""
    traj, times = defaultdict(dict), defaultdict(dict)
    by = defaultdict(list)
    for r in rows:
        by[r["arm"], r["part"]].append(r)
    for (arm, part), rs in by.items():
        rs.sort(key=lambda r: r["round"])
        cur, ys, ts = None, [], []
        for r in rs:
            if r["round"] == 0 or r.get("accepted"):
                cur = r.get("iou3d")
            ys.append(cur)
            ts.append(r.get("wall_seconds", 0))
        traj[arm][part], times[arm][part] = ys, ts
    return traj, times


def plot_rounds(traj, out):
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for arm, parts in sorted(traj.items()):
        n = max(len(v) for v in parts.values())
        ys = [np.nanmean([v[min(i, len(v) - 1)] if v[min(i, len(v) - 1)] is not None else np.nan
                          for v in parts.values()]) for i in range(n)]
        ax.plot(range(n), ys, "-o", ms=3, color=COLORS.get(arm), label=arm)
    ax.set_xlabel("round")
    ax.set_ylabel("mean 3D IoU (kept program)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "iou_by_round.png", dpi=200)
    plt.close(fig)


def plot_time(traj, times, out):
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for arm, parts in sorted(traj.items()):
        n = max(len(v) for v in parts.values())
        ys = [np.nanmean([v[min(i, len(v) - 1)] if v[min(i, len(v) - 1)] is not None else np.nan
                          for v in parts.values()]) for i in range(n)]
        ts = [np.mean([t[min(i, len(t) - 1)] for t in times[arm].values()]) / 60 for i in range(n)]
        ax.plot(ts, ys, "-o", ms=3, color=COLORS.get(arm), label=arm)
    ax.set_xlabel("mean wall time per part (min)")
    ax.set_ylabel("mean 3D IoU (kept program)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "iou_vs_time.png", dpi=200)
    plt.close(fig)


def plot_outcomes(rows, out):
    arms = sorted({r["arm"] for r in rows})
    cats = [("kept", "good", "#1a9e5a"), ("kept", "neutral", "#a6d8b9"), ("kept", "bad", "#c23b3b"),
            ("dropped", "good", "#f2b6b6"), ("dropped", "neutral", "#dddddd"), ("dropped", "bad", "#7fa7e0")]
    counts = {a: {c: 0 for c in cats} for a in arms}
    for r in rows:
        if r["round"] > 0 and r.get("status") == "ok":
            k = "kept" if r.get("accepted") else "dropped"
            o = outcome(r)
            for c in cats:
                if c[0] == k and c[1] == o:
                    counts[r["arm"]][c] += 1
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    left = np.zeros(len(arms))
    for c in cats:
        v = np.array([counts[a][c] for a in arms])
        ax.barh(arms, v, left=left, color=c[2], label=f"{c[0]} {c[1]}")
        left += v
    ax.set_xlabel("edits")
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "edit_outcomes.png", dpi=200)
    plt.close(fig)


def montage(root, part, finals, target_root, out, view="iso_fr", tile=220):
    arms = sorted(a for p, a in finals if p == part)
    if not arms:
        return
    tdir = None
    if target_root is not None and (target_root / part).exists():
        tdir = target_root / part
    cols = [("target", tdir / f"{view}.png" if tdir else None, None),
            ("first", root / part / "init" / f"{view}.png", root / part / "init" / "compare" / f"{view}_overlay.png")]
    for a in arms:
        d = Path(finals[part, a]["final_dir"])
        iou = finals[part, a].get("iou3d")
        cols.append((f"{a} {iou:.3f}" if iou is not None else a, d / f"{view}.png",
                     d / "compare" / f"{view}_overlay.png"))
    sheet = Image.new("RGB", (tile * len(cols), 2 * tile), (255, 255, 255))
    for i, (lab, img, ov) in enumerate(cols):
        for j, p in enumerate((img, ov)):
            if p is not None and Path(p).exists():
                im = Image.open(p).convert("RGB").resize((tile, tile), Image.LANCZOS)
                if j == 0:
                    ImageDraw.Draw(im).text((5, 4), lab, fill=(0, 0, 0))
                sheet.paste(im, (i * tile, j * tile))
    sheet.save(out / f"montage_{part}.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path)
    ap.add_argument("--targets", type=Path, default=Path("out/targets/fusion360"))
    ap.add_argument("--montages", type=int, default=6, help="how many parts get a montage")
    args = ap.parse_args()
    rows, finals = load(args.root)
    out = args.root / "figures"
    out.mkdir(exist_ok=True)
    traj, times = kept_trajectories(rows)
    plot_rounds(traj, out)
    plot_time(traj, times, out)
    plot_outcomes(rows, out)
    for part in sorted({p for p, _ in finals})[:args.montages]:
        montage(args.root, part, finals, args.targets, out)
    print(f"wrote figures to {out}")


if __name__ == "__main__":
    main()
