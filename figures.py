"""Figures for the report/poster from a refine.py run folder.

    uv run python figures.py runs/<run>            # -> runs/<run>/results/figures/*.png
    (refine.py already does this as it goes, via report.py)

  iou_by_round.png    mean hidden 3D IoU of the kept program after each round, per arm
  iou_vs_time.png     the same against cumulative wall time (GATOR Fig. 6 style)
  edit_outcomes.png   kept / dropped edits split by what they did to the hidden shape
Per-part image comparisons are parts/<part>/compare.png (report.py).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from progress import ARM_COLORS as COLORS  # noqa: E402  (one colour per arm everywhere)
from summarize_runs import load, outcome  # noqa: E402


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
    nmax = 1
    for arm, parts in sorted(traj.items()):
        n = max(len(v) for v in parts.values())
        ys = [np.nanmean([v[min(i, len(v) - 1)] if v[min(i, len(v) - 1)] is not None else np.nan
                          for v in parts.values()]) for i in range(n)]
        ax.plot(range(n), ys, "-o", ms=3, color=COLORS.get(arm), label=arm)
        nmax = max(nmax, n)
    ax.set_xticks(range(nmax))
    ax.set_xticklabels(["start"] + [str(i) for i in range(1, nmax)])
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


OUTCOME_COLORS = {"good": "#1a9e5a", "neutral": "#c4c4c0", "bad": "#c23b3b"}
OUTCOME_LABELS = {"good": "improved 3D IoU", "neutral": "no real change", "bad": "hurt 3D IoU"}


def plot_outcomes(rows, out):
    """Per arm, one bar for kept edits and one for dropped edits, each split by what the
    edit did to the hidden shape. Good decisions: kept+improved, dropped+hurt."""
    arms = sorted({r["arm"] for r in rows})
    outs = ["good", "neutral", "bad"]
    counts = {(a, k): {o: 0 for o in outs} for a in arms for k in ("kept", "dropped")}
    for r in rows:
        if r["round"] > 0 and r.get("status") == "ok":
            k = "kept" if r.get("accepted") else "dropped"
            counts[r["arm"], k][outcome(r)] += 1

    # y positions: arms top to bottom, kept above dropped inside each arm
    ys, labels, keys = [], [], []
    for i, a in enumerate(arms):
        for j, k in enumerate(("kept", "dropped")):
            ys.append(-(i * 3 + j))
            labels.append(k)
            keys.append((a, k))
    fig, ax = plt.subplots(figsize=(5.5, 0.9 + 0.75 * len(arms)))
    left = np.zeros(len(keys))
    for o in outs:
        v = np.array([counts[key][o] for key in keys], dtype=float)
        ax.barh(ys, v, left=left, height=0.8, color=OUTCOME_COLORS[o],
                edgecolor="white", linewidth=1.5, label=OUTCOME_LABELS[o])
        for y, l, n in zip(ys, left, v):
            if n:
                ax.text(l + n / 2, y, f"{int(n)}", ha="center", va="center", fontsize=7,
                        color="white" if o != "neutral" else "#333333")
        left += v
    for y, key, end in zip(ys, keys, left):
        ax.text(end + 0.15, y, f"{int(sum(counts[key].values()))} total",
                va="center", fontsize=7, color="#666666")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8)
    for i, a in enumerate(arms):  # arm name to the left of its pair of bars
        ax.text(-0.16, -(i * 3 + 0.5), a, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=9, fontweight="bold", color=COLORS.get(a, "#333"))
    ax.set_xlabel("edits (built and checked)")
    ax.set_xlim(0, left.max() * 1.15 + 1)
    ax.xaxis.get_major_locator().set_params(integer=True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(out / "edit_outcomes.png", dpi=200)
    plt.close(fig)


def write_figures(root: Path) -> Path:
    rows, _ = load(root)
    out = root / "results" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    if rows:
        traj, times = kept_trajectories(rows)
        plot_rounds(traj, out)
        plot_time(traj, times, out)
        plot_outcomes(rows, out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    print(f"wrote figures to {write_figures(args.root)}")


if __name__ == "__main__":
    main()
