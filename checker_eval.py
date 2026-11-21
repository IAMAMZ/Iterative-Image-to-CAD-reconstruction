"""Stage 2: how reliable is the geometric checker when the target's masks and depth are noisy?

The loop keeps an edit when geo_accept() says the candidate got closer to the target
views. This script measures, without any VLM calls, how often that decision is right
as the target observations get worse (corrupt.py), with and without view weights:

  1. per part: the starting program plus K random edits of it (one number scaled by
     x0.75..1.3, including subtle x0.95 / x1.05, or shifted if it is 0), built once against the CLEAN target and scored
     once against the hidden 3D shape (3D IoU, offline only);
  2. every ordered pair (A -> B) of those programs is one proposed edit; its true label
     is beneficial / harmful / neutral by 3D IoU (refine.verdict_of, +-0.005);
  3. for each condition (clean, and every <kind>_L<level> from corrupt.py) the same
     candidates are compared with that condition's target views and geo_accept decides
     each edit, once with the view weights of that target and once without.

Building and 3D scoring happen once per candidate; each condition only re-runs the cheap
2D comparison, so a full sweep costs minutes of CPU and no API calls.

    uv run python corrupt.py data/generated/targets/fusion360 --split data/fusion360/stage1.txt
    uv run python checker_eval.py data/generated/targets/fusion360 \
        --init data/generated/init/cadrille_rl --edits 8 --name stage2_checker
    # -> runs/<date>_stage2_checker/README.md

Simplification (stated in docs/STAGE2.md): candidates are centred with the CLEAN target's
measured bbox centre. In the loop the centre comes from the noisy target, but it is the
same for both sides of an edit, so it shifts both and barely changes the decision.
"""
import argparse
import csv
import datetime
import json
import random
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import layout
from compare import load_views, view_metrics
from corrupt import KINDS, condition_name
from geo_check import geo_accept, geo_score
from rig import load_rig
from view_weights import measure_bbox, view_weights

ROOT = Path(__file__).parent
FACTORS = (0.75, 0.9, 0.95, 1.05, 1.1, 1.3)   # subtle and coarse edits
SHIFTS = (-15, -5, 5, 15)          # for literals that are 0 (cadrille units, part ~200 long)
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
MODES = ("weights", "no_weights")
SMALL = 0.02   # |change in 3D IoU| up to this is a "subtle" edit (beneficial/harmful start at 0.005)
BLUE, ORANGE = "#2a78d6", "#eb6834"   # categorical slots 1-2 (dataviz palette, validated)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


# ------------------------------------------------------------------ edits
def perturb(src: str, rng: random.Random) -> tuple[str, str] | None:
    """Change one numeric literal of a program. -> (new source, description) or None."""
    lines = src.splitlines(keepends=True)
    spots = [(i, m) for i, l in enumerate(lines) if not l.lstrip().startswith(("import", "#"))
             for m in NUM.finditer(l)]
    if not spots:
        return None
    i, m = rng.choice(spots)
    old = float(m.group())
    new = old + rng.choice(SHIFTS) if old == 0 else old * rng.choice(FACTORS)
    txt = f"{new:.4g}"
    lines[i] = lines[i][:m.start()] + txt + lines[i][m.end():]
    return "".join(lines), f"line {i + 1}: {m.group()} -> {txt}"


def make_candidates(target: Path, init: Path, out: Path, k: int, seed: int, center, jobs: int):
    """Build the starting program and k valid random edits of it against the clean target,
    score each against gt.stl. Cached: existing candidates are reused. -> list of dicts."""
    from eval3d import evaluate
    from refine import build
    out.mkdir(parents=True, exist_ok=True)
    meta_f = out / "candidates.json"
    if meta_f.exists():
        meta = json.loads(meta_f.read_text())
        if len(meta) >= k + 1:
            return meta[:k + 1]
    base = init.read_text()
    rng = random.Random(f"{seed}|{target.name}")
    todo = [("c00", base, "starting program")]
    seen = {base}
    while len(todo) < 3 * k + 1:                 # spare edits in case some fail to build
        p = perturb(base, rng)
        if p is None:
            break
        if p[0] not in seen:
            seen.add(p[0])
            todo.append((f"c{len(todo):02d}", p[0], p[1]))

    def one(item):
        name, src, desc = item
        d = out / name
        if d.exists():
            shutil.rmtree(d)
        err = build(src, d, target, center)
        if err and name == "c00":            # retry once: a transient failure (e.g. the
            err = build(src, d, target, center)   # machine slept) must not drop the part
        if err:
            if name == "c00":
                print(f"  {target.name}: starting program failed to build: {err[-300:]}",
                      flush=True)
            return None
        e = evaluate(target, d)
        return {"name": name, "edit": desc, "dir": str(d), "iou3d": e.get("iou3d")}

    meta = []
    with ThreadPoolExecutor(jobs) as ex:
        first = list(ex.map(one, todo[:k + 1]))
        meta = [m for m in first if m]
        rest = iter(todo[k + 1:])
        while len(meta) < k + 1:
            batch = [x for _, x in zip(range(k + 1 - len(meta)), rest)]
            if not batch:
                break
            meta += [m for m in ex.map(one, batch) if m]
    if not meta or meta[0]["name"] != "c00":
        return []                                 # the starting program itself did not build
    meta = [m for m in meta if m["iou3d"] is not None]
    if len(meta) < 2:
        print(f"  {target.name}: no 3D IoU for its programs (GT mesh not watertight?)",
              flush=True)
        return []
    meta_f.write_text(json.dumps(meta, indent=2) + "\n")
    return meta


# ------------------------------------------------------------------ scoring
def report_for(target_views, mm, cand_views) -> dict:
    """The part of compare.compare's report that geo_check needs, without writing images."""
    return {"mm_per_unit": mm,
            "views": {v: view_metrics(mt, dt, *cand_views[v], mm)
                      for v, (mt, dt) in target_views.items()}}


def spearman(a, b) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    return float(np.corrcoef(ra, rb)[0, 1])


def evaluate_part(cands, target: Path, cond: str, rig):
    """All ordered pairs of one part under one condition. -> (pair rows, part row)."""
    from refine import verdict_of
    tv, tinfo = load_views(target)
    mm = 1.0 / tinfo["normalization"]["scale"]
    w = view_weights(target, rig)
    hit = tinfo.get("corruption", {}).get("views", [])
    reps = [report_for(tv, mm, c["views"]) for c in cands]
    rows = []
    for mode in MODES:
        ww = w if mode == "weights" else None
        for i, a in enumerate(cands):
            for j, b in enumerate(cands):
                if i == j:
                    continue
                verdict = verdict_of(a["iou3d"], b["iou3d"])
                keep, det = geo_accept(reps[i], reps[j], ww)
                rows.append({"part": target.name, "condition": cond, "mode": mode,
                             "from": a["name"], "to": b["name"], "verdict": verdict,
                             "keep": keep, "gain": det["gain"],
                             "inconclusive": det["inconclusive"],
                             "iou3d_from": a["iou3d"], "iou3d_to": b["iou3d"]})
    part = {"part": target.name, "condition": cond,
            "rho_weights": spearman([geo_score(r, w) for r in reps], [c["iou3d"] for c in cands]),
            "rho_no_weights": spearman([geo_score(r) for r in reps], [c["iou3d"] for c in cands]),
            "hit_weight": float(np.mean([w[v] for v in hit])) if hit else None,
            "other_weight": float(np.mean([x for v, x in w.items() if v not in hit])) if
            len(hit) < len(w) else None}
    return rows, part


def summarize(rows, parts):
    """-> one row per (condition, mode)."""
    out = []
    conds = list(dict.fromkeys(r["condition"] for r in rows))
    for c in conds:
        for mode in MODES:
            rs = [r for r in rows if r["condition"] == c and r["mode"] == mode]
            sig = [r for r in rs if r["verdict"] in ("beneficial", "harmful")]
            harm = [r for r in sig if r["verdict"] == "harmful"]
            good = [r for r in sig if r["verdict"] == "beneficial"]
            kept = [r for r in sig if r["keep"]]
            small = [r for r in sig if abs(r["iou3d_to"] - r["iou3d_from"]) <= SMALL]
            large = [r for r in sig if abs(r["iou3d_to"] - r["iou3d_from"]) > SMALL]
            right = lambda xs: [r for r in xs if r["keep"] == (r["verdict"] == "beneficial")]
            ps = [p for p in parts if p["condition"] == c]
            rho = [p[f"rho_{mode}"] for p in ps if p[f"rho_{mode}"] is not None]
            hw = [p["hit_weight"] for p in ps if p["hit_weight"] is not None]
            ow = [p["other_weight"] for p in ps if p["other_weight"] is not None]
            f = lambda xs, n: (len(xs) / n) if n else None
            out.append({
                "condition": c, "mode": mode, "parts": len(ps), "edits": len(sig),
                "accuracy": f(right(sig), len(sig)),
                "accuracy_small": f(right(small), len(small)),
                "accuracy_large": f(right(large), len(large)),
                "small_edits": len(small),
                "harmful_accept": f([r for r in harm if r["keep"]], len(harm)),
                "beneficial_recall": f([r for r in good if r["keep"]], len(good)),
                "kept_precision": f([r for r in kept if r["verdict"] == "beneficial"], len(kept)),
                "inconclusive": f([r for r in sig if r["inconclusive"]], len(sig)),
                "spearman": float(np.mean(rho)) if rho else None,
                "corrupted_view_weight": float(np.mean(hw)) if hw else None,
                "other_view_weight": float(np.mean(ow)) if ow else None,
            })
    return out


# ------------------------------------------------------------------ outputs
def _fmt(x, pct=False):
    if x is None:
        return "-"
    return f"{100 * x:.0f}%" if pct else f"{x:.2f}"


def figure(summary, out_png: Path, metric="accuracy", label="edit decisions that are right"):
    """Small multiples: one panel per corruption kind, x = level (0 = clean), one line per
    mode. Blue solid circles = view weights on, orange dashed squares = off."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    by = {(s["condition"], s["mode"]): s[metric] for s in summary}
    kinds = [k for k in KINDS if any(c.startswith(k + "_L") for c, _ in by)]
    if not kinds:
        return None
    ncol = 4
    nrow = -(-len(kinds) // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.6 * ncol, 2.3 * nrow + 0.6), sharey=True,
                             squeeze=False, facecolor="#fcfcfb")
    style = {"weights": dict(color=BLUE, ls="-", marker="o", label="view weights on"),
             "no_weights": dict(color=ORANGE, ls="--", marker="s", label="view weights off")}
    for ax in axes.flat[len(kinds):]:
        ax.axis("off")
    for ax, k in zip(axes.flat, kinds):
        ax.set_facecolor("#fcfcfb")
        for mode in MODES:
            xs, ys = [], []
            for lv in (0, 1, 2, 3):
                y = by.get((condition_name(k, lv), mode))
                if y is not None:
                    xs.append(lv)
                    ys.append(100 * y)
            ax.plot(xs, ys, lw=2, ms=6, mec="#fcfcfb", mew=1.5, **style[mode])
        ax.set_title(k, fontsize=10, color=INK, loc="left")
        ax.set_xticks([0, 1, 2, 3], ["clean", "L1", "L2", "L3"], fontsize=8, color=INK2)
        ax.tick_params(axis="y", labelsize=8, colors=INK2, length=0)
        ax.tick_params(axis="x", length=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
    for ax in axes[:, 0]:
        ax.set_ylabel("%", fontsize=8, color=INK2)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=2, frameon=False, fontsize=9)
    fig.suptitle(f"Geometric checker under noisy target views: {label} (%)", x=0.01, ha="left",
                 fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


def write_readme(out: Path, summary, cfg):
    cols = [("accuracy", "right decisions", True), ("accuracy_small", "right (subtle)", True),
            ("harmful_accept", "harmful kept", True),
            ("beneficial_recall", "good kept", True), ("kept_precision", "kept that helped", True),
            ("spearman", "rank corr.", False), ("corrupted_view_weight", "w(hit views)", False),
            ("other_view_weight", "w(other views)", False)]
    head = "| condition | view weights | edits | " + " | ".join(c[1] for c in cols) + " |"
    lines = [head, "|" + "---|" * (3 + len(cols))]
    for s in summary:
        lines.append(f"| {s['condition']} | {'on' if s['mode'] == 'weights' else 'off'} | "
                     f"{s['edits']} | " + " | ".join(_fmt(s[c], p) for c, _, p in cols) + " |")
    (out / "README.md").write_text(f"""# Checker under noise: {out.name}

Started {cfg['started']} · {cfg['n_parts']} parts · {cfg['edits']} random edits per part
(+ the starting program) · every ordered pair is one proposed edit · seed {cfg['seed']}.

**Question.** When the target masks and depth are corrupted (corrupt.py), how often does
`geo_accept` still keep the edits that truly help (3D IoU up by more than 0.005) and reject the
ones that hurt? Do the view weights help? Neutral edits (|change in 3D IoU| <= 0.005) are left
out of the rates.

![accuracy](results/figures/checker_accuracy.png)

![subtle edits](results/figures/checker_accuracy_subtle.png)

![harmful kept](results/figures/checker_harmful_accept.png)

## Table

{chr(10).join(lines)}

## Terms

- **right decisions**: kept a beneficial edit or rejected a harmful one.
- **right (subtle)**: the same, only for edits that changed 3D IoU by 0.005-0.02: the
  small corrections late rounds make, where noise in the views matters most.
- **harmful kept**: share of harmful edits the checker kept (lower is better).
- **good kept**: share of beneficial edits the checker kept (higher is better).
- **kept that helped**: of the edits it kept, the share that were beneficial.
- **rank corr.**: Spearman correlation, per part, between the geo score of each candidate
  and its hidden 3D IoU, averaged over parts (1 = the checker ranks programs exactly like 3D
  IoU).
- **w(hit views)** / **w(other views)**: mean view weight of the views the corruption touched
  / did not touch. For pervasive corruptions every view is hit.

Files: `results/summary.csv`, `results/pairs.csv` (every decision), `results/parts.csv`,
`candidates/<part>/` (the programs, renders and 3D scores, reused by later runs),
`config.json`.
""")


def _csv(path: Path, rows):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", type=Path, help="folder of clean target folders")
    ap.add_argument("--init", type=Path, required=True, help="folder of <part>.py programs")
    ap.add_argument("--noisy", type=Path, help="corrupt.py output (default <targets>_noisy)")
    ap.add_argument("--conditions", nargs="+",
                    help="condition folder names (default: every folder in --noisy)")
    ap.add_argument("--split", type=Path, help="only parts listed in this file")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--edits", type=int, default=8, help="random edits per part")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=4, help="parallel builds")
    ap.add_argument("--name", default="stage2_checker")
    ap.add_argument("--out", type=Path, help="exact run folder (default runs/<date>_<name>)")
    args = ap.parse_args(argv)

    noisy = args.noisy or args.targets.with_name(args.targets.name + "_noisy")
    conds = args.conditions or sorted(p.name for p in noisy.iterdir() if p.is_dir())
    out = args.out or ROOT / "runs" / f"{datetime.date.today():%Y-%m-%d}_{args.name}"
    out.mkdir(parents=True, exist_ok=True)
    parts = sorted(p for p in args.targets.iterdir() if layout.is_rendered(p))
    if args.split:
        keep = set(args.split.read_text().split())
        parts = [p for p in parts if p.name in keep]
    parts = [p for p in parts if (args.init / f"{p.name}.py").exists()][:args.limit]
    cfg = {"started": f"{datetime.datetime.now():%Y-%m-%d %H:%M}", "n_parts": len(parts),
           "edits": args.edits, "seed": args.seed, "conditions": ["clean", *conds],
           "targets": str(args.targets), "noisy": str(noisy), "init": str(args.init)}
    (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    rig = load_rig()
    rows, part_rows = [], []
    for n, target in enumerate(parts, 1):
        lo, hi = measure_bbox(target, rig)
        cands = make_candidates(target, args.init / f"{target.name}.py",
                                out / "candidates" / target.name, args.edits, args.seed,
                                (lo + hi) / 2, args.jobs)
        if len(cands) < 2:
            print(f"[{n}/{len(parts)}] {target.name}: skipped (see the line above)")
            continue
        for c in cands:
            c["views"] = load_views(Path(c["dir"]))[0]
        for cond in ["clean", *conds]:
            t = target if cond == "clean" else noisy / cond / target.name
            if not layout.is_rendered(t):
                continue
            r, p = evaluate_part(cands, t, cond, rig)
            rows += r
            part_rows.append(p)
        ious = [c["iou3d"] for c in cands]
        print(f"[{n}/{len(parts)}] {target.name}: {len(cands)} programs, 3D IoU "
              f"{min(ious):.2f}-{max(ious):.2f}", flush=True)
        for c in cands:
            del c["views"]
    summary = summarize(rows, part_rows)
    res = out / "results"
    _csv(res / "pairs.csv", rows)
    _csv(res / "parts.csv", part_rows)
    _csv(res / "summary.csv", summary)
    (res / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    figure(summary, res / "figures" / "checker_accuracy.png")
    figure(summary, res / "figures" / "checker_accuracy_subtle.png", "accuracy_small",
           "subtle edit decisions that are right")
    figure(summary, res / "figures" / "checker_harmful_accept.png", "harmful_accept",
           "harmful edits kept")
    write_readme(out, summary, cfg)
    print(f"done: {out / 'README.md'}")


if __name__ == "__main__":
    main()
