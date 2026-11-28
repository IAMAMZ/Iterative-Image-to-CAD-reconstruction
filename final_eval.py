"""Final evaluation of the ablation runs: one 3D score per config and part, recomputed from
the final program, never used inside the loop.

    uv run python final_eval.py                                  # every runs/*_abl_* folder
    uv run python final_eval.py --parts data/fusion360/ablation_batch1.txt
    uv run python final_eval.py --glob 'runs/*_pilot*' --parts data/fusion360/tuning.txt

For every config (a run folder plus its `_part2`, `_part3` ... folders) and every expected part:
  * the final state (result.json `final_dir`: the last kept program) is scored again against
    the hidden gt.stl with eval3d.evaluate: 3D IoU, Chamfer (x1000, normalised frame), the
    cadrille-protocol IoU and CD, Hausdorff, F1. A fresh recompute, so it also checks the
    numbers logged during the run.
  * IoU rule (a): a final program whose IoU cannot be computed (an open, non-watertight
    solid, or a failed boolean) scores IoU 0, counted as a failure. Chamfer is still
    reported for it, since it only needs surface samples.
  * parts whose GT mesh itself is open (not watertight) get no IoU at all (it would measure
    the GT's defect, not the method); they still count for Chamfer.
  * a part with no result.json is "missing" (crashed / never ran): rerun it as _partN
    (check_runs.py prints the command); it is left out, with a warning.
Per config: mean and median IoU, failures, median and mean Chamfer, and the paired
difference against the same machine's reference (runbook B's configs vs main_s1, the rest
vs main): mean dIoU with a bootstrap 95% CI over parts, wins / ties / losses, Wilcoxon p,
and the median dChamfer.

Writes <out>/final_eval.csv (one row per config and part) and <out>/README.md.
Reads files only; never calls a model.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
PART_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_(?P<base>.+?)(?:_part(?P<n>\d+))?$")
B_CONFIGS = {"abl_main_s1", "abl_gemini", "abl_one_view", "abl_no_gate", "abl_patience1",
             "abl_patience2", "abl_no_detail", "abl_no_kernel", "abl_signed_resid"}
TIE = 0.005          # |dIoU| below this is a tie
METRICS = ("iou3d", "chamfer_x1000", "iou3d_cad", "cd_cad", "hausdorff", "f1")


def configs(glob: str):
    """{config name: [run folders]} with _partN folders merged into their base."""
    out = defaultdict(list)
    for d in sorted(ROOT.glob(glob)):
        m = PART_RE.match(d.name)
        if d.is_dir() and m and (d / "config.json").exists():
            out[m["base"]].append(d)
    return dict(out)


def find_results(run_dirs):
    """{part: (result.json path, run dir)}; a later _partN wins over an earlier folder."""
    found = {}
    for rd in run_dirs:
        for f in sorted(rd.glob("parts/*/*/result.json")):
            found[f.parts[-3]] = (f, rd)
    return found


def target_of(run_dir: Path, part: str) -> Path:
    t = Path(json.loads((run_dir / "config.json").read_text())["targets"][part])
    return t if t.is_absolute() else ROOT / t


def score(job):
    """One part of one config -> row (runs in a worker process)."""
    import trimesh
    import eval3d
    cfg, part, res_path, run_dir = job
    res = json.loads(Path(res_path).read_text())
    final = Path(res["final_dir"])
    if not final.is_absolute():
        final = Path(res_path).parent / final
    tgt = target_of(Path(run_dir), part)
    row = {"config": cfg, "part": part, "run": Path(run_dir).name, "final": final.name,
           "stop": res.get("stop"), "rounds_run": res.get("rounds_run"),
           "logged_iou3d": res.get("iou3d"), "logged_chamfer_x1000": res.get("chamfer_x1000")}
    gt_closed = trimesh.load(tgt / "gt.stl", force="mesh").is_watertight
    try:
        cand_closed = trimesh.load(final / "solid.stl", force="mesh").is_watertight
        m = eval3d.evaluate(tgt, final)
    except Exception as e:  # noqa: BLE001 - one bad part must not stop the evaluation
        cand_closed, m = False, {}
        row["note"] = f"evaluate failed: {type(e).__name__}: {e}"[:200]
    row.update({k: m.get(k) for k in METRICS})
    row.update(gt_watertight=gt_closed, final_watertight=cand_closed)
    if not gt_closed:
        row["iou_rule"] = "gt_open"           # no IoU: the GT is broken, not the method
        row["iou3d_scored"] = None
    elif m.get("iou3d") is None:
        row["iou_rule"] = "fail_0"            # rule (a)
        row["iou3d_scored"] = 0.0
    else:
        row["iou_rule"] = "ok"
        row["iou3d_scored"] = m["iou3d"]
    return row


def boot_ci(d, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    means = rng.choice(d, (n, len(d)), replace=True).mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(rows_a, rows_ref, key, positive_is_better=True):
    a = {r["part"]: r[key] for r in rows_a if r.get(key) is not None}
    b = {r["part"]: r[key] for r in rows_ref if r.get(key) is not None}
    common = sorted(set(a) & set(b))
    if not common:
        return None
    d = np.array([a[p] - b[p] for p in common])
    if not positive_is_better:
        d = -d
    out = {"n": len(common), "mean": float(d.mean()), "median": float(np.median(d)),
           "wins": int((d > TIE).sum()), "ties": int((abs(d) <= TIE).sum()),
           "losses": int((d < -TIE).sum())}
    if len(common) >= 2:
        out["ci"] = boot_ci(d)
    try:
        from scipy.stats import wilcoxon
        out["p"] = float(wilcoxon(d).pvalue) if np.any(d != 0) and len(common) >= 5 else None
    except Exception:  # noqa: BLE001
        out["p"] = None
    return out


def fmt(x, f="{:.3f}"):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f.format(x)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glob", default="runs/*_abl_*")
    ap.add_argument("--parts", type=Path, default=ROOT / "data/fusion360/ablation.txt")
    ap.add_argument("--out", type=Path, default=ROOT / "runs/ablation_final")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    expected = [l.strip() for l in args.parts.read_text().splitlines() if l.strip()]
    cfgs = configs(args.glob)
    if not cfgs:
        raise SystemExit(f"no run folders match {args.glob}")

    jobs, missing = [], {}
    for cfg, dirs in cfgs.items():
        found = find_results(dirs)
        missing[cfg] = [p for p in expected if p not in found]
        jobs += [(cfg, p, str(found[p][0]), str(found[p][1])) for p in expected if p in found]
    print(f"scoring {len(jobs)} final programs from {len(cfgs)} configs ...", flush=True)
    with ProcessPoolExecutor(args.jobs) as ex:
        rows = list(ex.map(score, jobs))

    args.out.mkdir(parents=True, exist_ok=True)
    cols = ["config", "part", "run", "final", "stop", "rounds_run", "iou_rule", "iou3d_scored",
            *METRICS, "gt_watertight", "final_watertight", "logged_iou3d",
            "logged_chamfer_x1000", "note"]
    with open(args.out / "final_eval.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["config"], r["part"])))

    by = defaultdict(list)
    for r in rows:
        by[r["config"]].append(r)
    # logged vs recomputed (a check on the run's own numbers)
    drift = [abs(r["iou3d"] - r["logged_iou3d"]) for r in rows
             if r.get("iou3d") is not None and r.get("logged_iou3d") is not None]

    L = [f"# Final evaluation ({args.glob}, {len(expected)} expected parts)", "",
         "Every final program re-scored against the hidden GT after the runs; nothing here was "
         "seen by the loop. IoU rule (a): a final program with no computable IoU (open solid) "
         f"scores 0. Parts with an open GT mesh get no IoU. Ties: |Δ| ≤ {TIE}.", "",
         "| config | parts | IoU mean | IoU median | IoU = 0 (open final) | GT open | "
         "Chamfer×1000 median | Chamfer mean | CD (cadrille) median | missing |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for cfg in sorted(by):
        rs = by[cfg]
        iou = [r["iou3d_scored"] for r in rs if r["iou3d_scored"] is not None]
        ch = [r["chamfer_x1000"] for r in rs if r.get("chamfer_x1000") is not None]
        cd = [r["cd_cad"] for r in rs if r.get("cd_cad") is not None]
        L.append(f"| {cfg} | {len(rs)} | {fmt(np.mean(iou) if iou else None)} | "
                 f"{fmt(np.median(iou) if iou else None)} | "
                 f"{sum(r['iou_rule'] == 'fail_0' for r in rs)} | "
                 f"{sum(r['iou_rule'] == 'gt_open' for r in rs)} | "
                 f"{fmt(np.median(ch) if ch else None, '{:.2f}')} | "
                 f"{fmt(np.mean(ch) if ch else None, '{:.2f}')} | "
                 f"{fmt(np.median(cd) if cd else None, '{:.4f}')} | {len(missing[cfg])} |")

    L += ["", "## Paired against the same machine's reference", "",
          "Δ = config − reference on the parts both have (IoU: higher is better; Chamfer: "
          "shown as reference − config, so positive is better too). CI: bootstrap 95% over parts.",
          "", "| config | reference | n | mean ΔIoU [95% CI] | W / T / L | Wilcoxon p | "
          "median ΔChamfer (better > 0) |", "|---|---|---|---|---|---|---|"]
    for cfg in sorted(by):
        ref = "abl_main_s1" if cfg in B_CONFIGS and cfg != "abl_main_s1" else "abl_main"
        if cfg == ref or ref not in by:
            continue
        pi = paired(by[cfg], by[ref], "iou3d_scored")
        pc = paired(by[cfg], by[ref], "chamfer_x1000", positive_is_better=False)
        if not pi:
            continue
        ci = pi.get("ci")
        L.append(f"| {cfg} | {ref} | {pi['n']} | {pi['mean']:+.3f} "
                 f"[{fmt(ci[0] if ci else None, '{:+.3f}')}, {fmt(ci[1] if ci else None, '{:+.3f}')}] | "
                 f"{pi['wins']} / {pi['ties']} / {pi['losses']} | {fmt(pi.get('p'))} | "
                 f"{fmt(pc['median'] if pc else None, '{:+.2f}')} |")
    if "abl_main_rep" in by and "abl_main" in by:
        L += ["", "`abl_main_rep` vs `abl_main` above is the **same-machine noise floor**: `main` run "
              "twice on the same machine. A config's ΔIoU smaller than this gap is not a finding."]
    if "abl_main_s1" in by and "abl_main" in by:
        L += ["", "`abl_main_s1` vs `abl_main` above is the noise floor: two runs of the same "
              "method (different seed and machine)."]

    notes = [f"- {r['config']} {r['part']}: {r['note']}" for r in rows if r.get("note")]
    notes += [f"- {r['config']} {r['part']}: final solid is open, IoU scored 0 (Chamfer "
              f"{fmt(r.get('chamfer_x1000'), '{:.2f}')})" for r in rows if r["iou_rule"] == "fail_0"]
    notes += [f"- {cfg}: missing {', '.join(ps)} (still running, or crashed: rerun as _partN)" for cfg, ps in missing.items() if ps]
    L += ["", "## Checks", "",
          f"- recomputed vs logged 3D IoU: max difference {fmt(max(drift) if drift else None, '{:.2e}')} "
          f"over {len(drift)} parts", *notes]
    (args.out / "README.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {args.out / 'final_eval.csv'} and README.md")


if __name__ == "__main__":
    main()
