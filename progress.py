"""Progression figures: how each arm's program changed round by round.

  parts/<part>/progress.png
      top:   the target (shape + depth) and a 3D IoU-by-round chart, one line per arm
      below: one strip per arm: start, round 1, round 2, ... Each tile is the shape (top) and
             its depth error against the target (bottom; pale = right, dark = wrong, red/blue
             = missing/extra material), from the one view where the starting program was
             most wrong. Frame and caption: green = kept, red = rejected, grey = no edit.
  results/figures/progress_by_part.png
      one small chart per part (worst start first): 3D IoU of the kept program by round,
      hollow dots = edits that were tried and rejected.

    uv run python progress.py runs/<run>     # (report.py calls this after every part)
"""
import argparse
import json
import textwrap
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import layout  # noqa: E402
from summarize_runs import load  # noqa: E402

# fixed colour per arm (validated categorical palette, slot order = how central the arm is)
ARM_COLORS = {"geo": "#2a78d6", "hybrid": "#eb6834", "vlm": "#1baf7a", "premise": "#eda100",
              "oracle": "#e87ba4", "gsolver": "#008300"}
STATUS = {"kept": ("#0ca30c", "✓ kept"), "rejected": ("#d03b3b", "✗ rejected"),
          "failed": ("#8c8c8c", "did not build"), "no-change": ("#8c8c8c", "no change"),
          "stopped": ("#8c8c8c", "stopped: all Yes"), "start": ("#5f5e5a", "start")}
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e1e0d9"
VIEWS = ("front", "right", "top", "iso_fr")

plt.rcParams.update({"font.size": 8, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})


# ------------------------------------------------------------------ data
def trajectories(rows):
    """{(part, arm): {"start", "kept": [iou of kept program after round 0..n],
    "rounds": [(round, outcome, candidate iou3d, dir name)]}}"""
    out = {}
    by = defaultdict(list)
    for r in rows:
        by[r["part"], r["arm"]].append(r)
    for key, rs in by.items():
        rs.sort(key=lambda r: r["round"])
        cur, kept, rounds = None, [], []
        for r in rs:
            if r["round"] == 0:
                cur = r.get("iou3d")
            else:
                d = r.get("dir")
                if d:                                # round_02_rejected -> rejected
                    outcome = d.split("_", 2)[-1]
                else:                                # runs from before outcome-named folders
                    d = f"round_{r['round']:02d}"
                    outcome = "kept" if r.get("accepted") else {
                        "ok": "rejected", "no_change": "no-change"}.get(r.get("status"),
                                                                        r.get("status"))
                rounds.append((r["round"], outcome, r.get("iou3d"), d))
                if r.get("accepted"):
                    cur = r.get("iou3d")
            kept.append(cur)
        out[key] = {"start": kept[0] if kept else None, "kept": kept, "rounds": rounds}
    return out


def worst_view(init_dir: Path) -> str:
    """The grid view where the starting program is most wrong (silhouette + depth), among
    views that show the part at a useful size (not edge-on)."""
    f = layout.diff_dir(init_dir) / "report.json"
    if not f.exists():
        return "iso_fr"
    rep = json.loads(f.read_text())
    vmax = rep.get("depth_vmax") or 0.05

    def err(m):
        sil = (m["missing_px"] + m["extra_px"]) / max(m["target_px"], 1)
        return sil + (m["depth_mae"] or 0) / vmax
    views = [v for v in VIEWS if v in rep["views"]]
    if not views:
        return "iso_fr"
    big = max(rep["views"][v]["target_px"] for v in views)
    views = [v for v in views if rep["views"][v]["target_px"] >= 0.35 * big]
    return max(views, key=lambda v: err(rep["views"][v]))


def _crop_box(target: Path | None, view: str, pad=0.08):
    if target is None or not layout.render(target, view, "_mask").exists():
        return None
    m = np.asarray(Image.open(layout.render(target, view, "_mask"))) > 0
    if not m.any():
        return None
    rr, cc = np.where(m)
    h, w = m.shape
    side = max(np.ptp(rr), np.ptp(cc)) * (1 + 2 * pad)
    cy, cx = (rr.min() + rr.max()) / 2, (cc.min() + cc.max()) / 2
    half = min(side / 2, h / 2, w / 2)
    cy, cx = np.clip(cy, half, h - half), np.clip(cx, half, w - half)
    return int(cx - half), int(cy - half), int(cx + half), int(cy + half)


def _stack(top: Path, bottom: Path, box):
    """shape over depth error, one image."""
    ims = []
    for p in (top, bottom):
        im = Image.open(p).convert("RGB") if p is not None and Path(p).exists() else \
            Image.new("RGB", (512, 512), (240, 240, 238))
        ims.append(im.crop(box) if box else im)
    w = ims[0].width
    out = Image.new("RGB", (w, ims[0].height + ims[1].height + 6), (255, 255, 255))
    out.paste(ims[0], (0, 0))
    out.paste(ims[1].resize((w, ims[1].height * w // ims[1].width)), (0, ims[0].height + 6))
    return np.asarray(out)


# ------------------------------------------------------------------ charts
def _iou_chart(ax, arms, traj, part, title=None, labels=True):
    n = 0
    ends = []
    for a in arms:
        t = traj.get((part, a))
        if not t or t["start"] is None:
            continue
        c = ARM_COLORS.get(a, MUTED)
        xs = list(range(len(t["kept"])))
        ys = [np.nan if y is None else y for y in t["kept"]]
        ax.step(xs, ys, where="post", color=c, lw=2, zorder=3, label=a)
        for rnd, outcome, iou, _ in t["rounds"]:
            if iou is None:
                continue
            if outcome == "kept":
                ax.plot(rnd, iou, "o", ms=6, color=c, mec="white", mew=1.5, zorder=4)
            else:                                    # tried, not kept
                ax.plot(rnd, iou, "o", ms=6, mfc="white", mec=c, mew=1.5, zorder=4)
        n = max(n, len(xs) - 1)
        ends.append((ys[-1], a, c))
    ax.set_xlim(-0.3, max(n, 1) + (0.9 if labels else 0.3))
    ax.set_xticks(range(n + 1))
    ax.set_xticklabels(["start"] + [str(i) for i in range(1, n + 1)])
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if labels:                                       # direct labels at the line ends
        ends = sorted((e for e in ends if not np.isnan(e[0])), reverse=True)
        lo, hi = ax.get_ylim()
        gap = (hi - lo) * 0.07
        last = hi + gap                              # stack downward from the top
        for y, a, c in ends:
            yl = min(y, last - gap)
            ax.text(n + 0.12, yl, f"{a} {y:.3f}", va="center", fontsize=8, color=INK)
            last = yl
    if title:
        ax.set_title(title, fontsize=8, loc="left", color=INK)


def part_figure(part_dir: Path, target: Path | None, arms, traj, start_name="start"):
    part = part_dir.name
    arms = [a for a in arms if (part, a) in traj]
    if not arms:
        return None
    view = worst_view(part_dir / "init")
    box = _crop_box(target, view)
    ncol = 1 + max(len(traj[part, a]["rounds"]) for a in arms)
    tile = 1.45
    height = 3.4 + 3.05 * len(arms)
    fig = plt.figure(figsize=(max(1.6 + tile * ncol, 7.5), height), facecolor="white")
    gs = fig.add_gridspec(1 + len(arms), 1 + ncol, height_ratios=[1.0] + [1.15] * len(arms),
                          width_ratios=[0.7] + [1] * ncol, hspace=0.35, wspace=0.08,
                          left=0.03, right=0.97, top=1 - 1.15 / height,
                          bottom=0.45 / height)
    fig.suptitle(f"{part}: how each arm's program changed, round by round", x=0.03, ha="left",
                 y=1 - 0.15 / height, va="top", fontsize=11, color=INK)
    fig.text(0.03, 1 - 0.45 / height, textwrap.fill(
        f"Tiles: shape (top) and depth error vs the target (bottom; pale = right, dark = "
        f"wrong) in the '{view}' view, where the start was most wrong. Numbers: 3D IoU (change "
        f"vs the program it edited).", int(fig.get_figwidth() * 15)), fontsize=8, color=MUTED,
        va="top")
    # header: target + chart
    ax = fig.add_subplot(gs[0, 1])
    if target is not None:
        ax.imshow(_stack(layout.render(target, view), layout.render(target, view, "_depth"), box))
    _frame(ax, INK, "target", f"{view}: shape / depth")
    ax = fig.add_subplot(gs[0, 2:] if ncol > 1 else gs[0, 1:])
    _iou_chart(ax, arms, traj, part)
    ax.set_ylabel("3D IoU")
    ax.set_title("line: kept program · ● edit kept · ○ edit rejected", fontsize=8,
                 loc="left", color=MUTED)
    # one strip per arm
    for i, a in enumerate(arms, start=1):
        t = traj[part, a]
        lab = fig.add_subplot(gs[i, 0])
        lab.axis("off")
        lab.add_patch(plt.Rectangle((0, 0.55), 0.12, 0.08, color=ARM_COLORS.get(a, MUTED),
                                    transform=lab.transAxes))
        lab.text(0.17, 0.59, a, fontsize=11, va="center", transform=lab.transAxes)
        end = t["kept"][-1]
        lab.text(0, 0.45, f"{_f(t['start'])} → {_f(end)}", fontsize=9, transform=lab.transAxes,
                 va="top")
        lab.text(0, 0.36, "start → final", fontsize=7, color=MUTED, transform=lab.transAxes,
                 va="top")
        tiles = [(part_dir / "init", "start", start_name, t["start"], None)]
        prev = t["start"]
        for rnd, outcome, iou, d in t["rounds"]:
            tiles.append((part_dir / a / d if d else None, outcome, f"round {rnd}", iou, prev))
            if outcome == "kept":
                prev = iou
        for j, (d, outcome, head, iou, before) in enumerate(tiles):
            ax = fig.add_subplot(gs[i, 1 + j])
            built = d is not None and layout.render(d, view).exists()
            color, word = STATUS.get(outcome, (MUTED, outcome))
            if built:
                ax.imshow(_stack(layout.render(d, view), layout.diff(d, view, "_depth_err"), box))
            else:                                   # nothing built this round: say why
                ax.set_aspect(2.1)
                ax.text(0.5, 0.5, word.replace(": ", ":\n"), ha="center", va="center",
                        color=MUTED, fontsize=9, transform=ax.transAxes)
                ax.set_facecolor("#f4f4f2")
            if outcome == "start":
                sub = _f(iou)
            elif not built:
                sub = ""
            else:
                sub = f"{word}\n{_f(iou)}" + ("" if iou is None or before is None
                                              else f" ({iou - before:+.3f})")
            _frame(ax, color, head, sub, lw=3 if outcome in ("kept", "rejected") else 1.2)
    out = part_dir / "progress.png"
    fig.savefig(out, dpi=110, facecolor="white")
    plt.close(fig)
    return out


def _frame(ax, color, head, sub, lw=1.2):
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(color)
        s.set_linewidth(lw)
    ax.set_title(head, fontsize=9, color=INK, pad=3)
    ax.set_xlabel(sub, fontsize=8, color=color if color != "#5f5e5a" else INK, labelpad=3)


def _f(x):
    return "–" if x is None else f"{x:.3f}"


def overview(root: Path, arms, traj, out: Path):
    parts = sorted({p for p, _ in traj}, key=lambda p: min(
        (traj[p, a]["start"] for a in arms if (p, a) in traj and traj[p, a]["start"] is not None),
        default=2))
    if not parts:
        return None
    ncols = min(3, len(parts))
    nrows = -(-len(parts) // ncols)
    fig, axs = plt.subplots(nrows, ncols, figsize=(3.4 * ncols, 2.5 * nrows + 0.8),
                            squeeze=False, sharey=True, facecolor="white")
    for ax, p in zip(axs.flat, parts):
        start = next((traj[p, a]["start"] for a in arms if (p, a) in traj), None)
        _iou_chart(ax, arms, traj, p, title=f"{p}  (start {_f(start)})")
    for ax in list(axs.flat)[len(parts):]:
        ax.axis("off")
    for ax in axs[:, 0]:
        ax.set_ylabel("3D IoU")
    handles = [plt.Line2D([], [], color=ARM_COLORS.get(a, MUTED), lw=2, label=a) for a in arms
               if any((p, a) in traj for p in parts)]
    handles += [plt.Line2D([], [], ls="", marker="o", color=MUTED, mec="white", ms=6,
                           label="edit kept"),
                plt.Line2D([], [], ls="", marker="o", mfc="white", mec=MUTED, ms=6,
                           label="edit tried, rejected")]
    fig.legend(handles=handles, loc="upper left", ncol=len(handles), frameon=False,
               bbox_to_anchor=(0.01, 0.995), fontsize=8)
    fig.suptitle("3D IoU of the kept program by round, per part (worst start first)", x=0.01,
                 y=0.955 if nrows > 1 else 0.9, ha="left", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93 if nrows > 1 else 0.85))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130, facecolor="white")
    plt.close(fig)
    return out


def write(root: Path, cfg=None, start_name="start"):
    root = Path(root)
    cfg = cfg if cfg is not None else json.loads((root / "config.json").read_text())
    rows, _ = load(root)
    traj = trajectories(rows)
    arms = cfg.get("arms") or sorted({a for _, a in traj})
    targets = {k: Path(v) for k, v in (cfg.get("targets") or {}).items()}
    for p in sorted({p for p, _ in traj}):
        t = targets.get(p)
        part_figure(root / "parts" / p, t if t and t.exists() else None, arms, traj, start_name)
    overview(root, arms, traj, root / "results" / "figures" / "progress_by_part.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path, help="a refine.py run folder")
    write(ap.parse_args().root)


if __name__ == "__main__":
    main()
