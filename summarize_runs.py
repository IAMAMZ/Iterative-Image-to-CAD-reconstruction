"""Summarise refine.py runs: compare the review methods (arms) on the same parts.

    uv run python summarize_runs.py runs/<run>   # prints tables; writes results/summary.json,
                                                 # results/parts.csv and results/edits.csv
(refine.py already does this as it goes, via report.py.)

Per arm:
  * shape quality vs the hidden GT at round 0 (cadrille / first program), at the end, at
    the best state the arm itself would pick (GT-free), and the oracle best round:
    median (IQR) and mean of 3D IoU, cadrille-protocol IoU/CD, Chamfer, Hausdorff, F1
  * compile/validity: invalid-proposal rate, repair success (built after >= 1 repair)
  * edit acceptance against what each edit really did to the hidden shape:
      kept-good / kept-bad / dropped-good / dropped-bad (+ neutral)
      kept precision = share of kept edits that helped; harmful acceptance rate
  * the same for the shadow decisions (what the geometric check, and the VLM judge where
    it ran, would have decided on the very same edits) and their agreement
  * change-type mix (structural / dimensional / positional), stop reasons, tokens, time
Per stratum (data/fusion360/stage1_meta.json: cadrille-IoU bin x mesh complexity), the
3D IoU gain of every arm.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
META = ROOT / "data" / "fusion360" / "stage1_meta.json"
METRICS = ("iou3d", "iou3d_cad", "cd_cad", "chamfer_x1000", "hausdorff", "f1", "iogt")


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


def med_iqr(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    q1, q2, q3 = np.percentile(xs, [25, 50, 75])
    return {"median": float(q2), "iqr": float(q3 - q1), "mean": float(np.mean(xs)), "n": len(xs)}


def outcome(e):
    return {"beneficial": "good", "harmful": "bad"}.get(e.get("verdict"), "neutral")


def decision_stats(edits, key):
    """Confusion of a decision (row[key] True/False) against the hidden-shape outcome."""
    c = Counter()
    for e in edits:
        d = e.get(key)
        if d is None:
            continue
        c[("kept-" if d else "dropped-") + outcome(e)] += 1
    kept = c["kept-good"] + c["kept-bad"] + c["kept-neutral"]
    bad = c["kept-bad"] + c["dropped-bad"]
    return {"counts": dict(c), "n": sum(c.values()),
            "kept_precision": c["kept-good"] / kept if kept else None,
            "harmful_accept_rate": c["kept-bad"] / bad if bad else None,
            "good_recall": c["kept-good"] / (c["kept-good"] + c["dropped-good"])
            if c["kept-good"] + c["dropped-good"] else None}


def load(root: Path):
    """Rows of every arm's log.jsonl and its result.json. Also reads runs made before the
    runs/ layout (<root>/<part>/<arm>/results.jsonl + final.json)."""
    new = (root / "parts").is_dir()
    log, res = ("parts/*/*/log.jsonl", "parts/*/*/result.json") if new else \
        ("*/*/results.jsonl", "*/*/final.json")
    rows = [json.loads(l) for f in sorted(root.glob(log))
            for l in f.read_text().splitlines() if l.strip()]
    finals = {}
    for f in root.glob(res):
        d = json.loads(f.read_text())
        finals[d["part"], d["arm"]] = d
    return rows, finals


def summarize(root: Path) -> dict:
    rows, finals = load(root)
    meta = json.loads(META.read_text())["parts"] if META.exists() else {}
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    out = {}
    for arm, rs in sorted(by_arm.items()):
        parts = sorted({r["part"] for r in rs})
        init = {r["part"]: r for r in rs if r["round"] == 0}
        fin = {p: finals[p, arm] for p in parts if (p, arm) in finals}
        edits = [r for r in rs if r["round"] > 0 and r.get("status") in ("ok", "failed")]
        valid = [e for e in edits if e["status"] == "ok"]
        quality = {}
        for m in METRICS:
            quality[m] = {
                "init": med_iqr([init[p].get(m) for p in init]),
                "final": med_iqr([f.get(m) for f in fin.values()]),
                "best_geo": med_iqr([f.get("best_geo", {}).get(m) for f in fin.values()]),
                "best_oracle": med_iqr([f.get("best_oracle", {}).get(m) for f in fin.values()]),
            }
        gains = [fin[p].get("iou3d") - init[p].get("iou3d") for p in fin
                 if p in init and fin[p].get("iou3d") is not None and init[p].get("iou3d") is not None]
        repaired = [e for e in valid if e.get("repairs_used", 0) > 0]
        needed = [e for e in edits if e.get("attempts", 1) > 1]
        both = [e for e in valid if e.get("vlm_decision") is not None]
        strata = defaultdict(list)
        for p in fin:
            if p in init and p in meta and fin[p].get("iou3d") is not None and init[p].get("iou3d") is not None:
                s = f"{meta[p]['iou_bin']}/{meta[p]['mesh']}"
                strata[s].append(fin[p]["iou3d"] - init[p]["iou3d"])
        out[arm] = {
            "parts": len(parts), "edits": len(edits),
            "quality": quality,
            "iou3d_gain": med_iqr(gains),
            "parts_improved": sum(g > 0.005 for g in gains), "parts_worse": sum(g < -0.005 for g in gains),
            "invalid_rate": (len(edits) - len(valid)) / len(edits) if edits else None,
            "repair_success": len(repaired) / len(needed) if needed else None,
            "acceptance": decision_stats(valid, "accepted"),
            "shadow_geo": decision_stats(valid, "geo_decision"),
            "shadow_vlm": decision_stats(valid, "vlm_decision"),
            "geo_vlm_agreement": (sum(e["geo_decision"] == e["vlm_decision"] for e in both) / len(both))
            if both else None,
            "change_types": dict(Counter(e.get("change_tag") or "untagged" for e in edits)),
            "stops": dict(Counter(f.get("stop") for f in fin.values())),
            "kernel_warnings_per_edit": mean([e.get("kernel_warnings") for e in valid]),
            "tokens_per_part": mean([f.get("prompt_tokens", 0) + f.get("output_tokens", 0) for f in fin.values()]),
            "llm_seconds_per_part": mean([f.get("llm_seconds") for f in fin.values()]),
            "wall_seconds_per_part": mean([f.get("wall_seconds") for f in fin.values()]),
            "gain_by_stratum": {k: med_iqr(v) for k, v in sorted(strata.items())},
        }
    write_csv(results_dir(root), rows, finals)
    return out


def results_dir(root: Path) -> Path:
    d = root / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_csv(root, rows, finals):
    keys = ["part", "arm", "stop", "rounds_run", "iou3d", "iou3d_cad", "cd_cad", "chamfer_x1000",
            "hausdorff", "f1", "w_iou", "llm_seconds", "prompt_tokens", "output_tokens",
            "wall_seconds"]
    init = {(r["part"], r["arm"]): r for r in rows if r["round"] == 0}
    with open(root / "parts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys + ["iou3d_init", "iou3d_best_oracle"])
        for (p, a), d in sorted(finals.items()):
            w.writerow([d.get(k) for k in keys] + [init.get((p, a), {}).get("iou3d"),
                                                   d.get("best_oracle", {}).get("iou3d")])
    ekeys = ["part", "arm", "round", "status", "accepted", "verdict", "geo_decision", "vlm_decision",
             "geo_gain", "geo_inconclusive", "change_tag", "iou3d_before", "iou3d", "w_iou",
             "qa_yes", "qa_n", "kernel_warnings", "repairs_used", "wall_seconds"]
    with open(root / "edits.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(ekeys)
        for r in rows:
            if r["round"] > 0:
                w.writerow([r.get(k) for k in ekeys])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path, help="a refine.py run folder (runs/<date>_<name>)")
    args = ap.parse_args()
    s = summarize(args.root)
    (results_dir(args.root) / "summary.json").write_text(json.dumps(s, indent=2) + "\n")
    f = lambda x, p=3: "  n/a" if x is None else f"{x:.{p}f}"
    mi = lambda d, p=3: "n/a" if d is None else f"{d['median']:.{p}f} ({d['iqr']:.{p}f})"
    for arm, m in s.items():
        q = m["quality"]
        print(f"[{arm}] {m['parts']} parts, {m['edits']} edits; stops {m['stops']}")
        for k, p in (("iou3d", 3), ("iou3d_cad", 3), ("cd_cad", 3), ("f1", 3)):
            print(f"  {k:10s} median (IQR)  init {mi(q[k]['init'], p)} -> final {mi(q[k]['final'], p)}"
                  f"   best(geo) {mi(q[k]['best_geo'], p)}   best(oracle) {mi(q[k]['best_oracle'], p)}")
        a, g, v = m["acceptance"], m["shadow_geo"], m["shadow_vlm"]
        print(f"  parts improved {m['parts_improved']}, worse {m['parts_worse']}; "
              f"invalid {f(m['invalid_rate'], 2)}, repair success {f(m['repair_success'], 2)}")
        for name, d in (("accepted", a), ("geo check", g), ("vlm judge", v)):
            if d["n"]:
                c = d["counts"]
                print(f"  {name:10s} kept good/bad/neutral {c.get('kept-good', 0)}/{c.get('kept-bad', 0)}/"
                      f"{c.get('kept-neutral', 0)}  dropped {c.get('dropped-good', 0)}/{c.get('dropped-bad', 0)}/"
                      f"{c.get('dropped-neutral', 0)}  precision {f(d['kept_precision'], 2)}  "
                      f"harmful-accept {f(d['harmful_accept_rate'], 2)}")
        print(f"  geo-vs-vlm agreement {f(m['geo_vlm_agreement'], 2)}; changes {m['change_types']}")
        print(f"  per part: {f(m['tokens_per_part'], 0)} tokens, {f(m['llm_seconds_per_part'], 0)} s model, "
              f"{f(m['wall_seconds_per_part'], 0)} s wall")


if __name__ == "__main__":
    main()
