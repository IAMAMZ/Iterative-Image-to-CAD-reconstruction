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
  * repeats: proposals that redo an attempt already rejected (or failed) from the same
    program, i.e. since the last kept edit (see `mark_repeats`)
Per stratum (data/fusion360/stage1_meta.json: cadrille-IoU bin x mesh complexity), the
3D IoU gain of every arm.
"""
import argparse
import csv
import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import vertex_ai

ROOT = Path(__file__).parent
META = ROOT / "data" / "fusion360" / "stage1_meta.json"
METRICS = ("iou3d", "iou3d_cad", "cd_cad", "chamfer_x1000", "hausdorff", "f1", "iogt")


# ------------------------------------------------------------------ repeats
NEAR = 0.9          # diff-text similarity that counts as the same edit
SAME_SPOT = 0.5     # share of edited tokens already edited by an earlier failed attempt
REWRITE = 0.75      # an edit touching more of the program than this is a rewrite: two rewrites
                    # always overlap, so they are not counted as a same-spot repeat
_NUM = re.compile(r"(?<![\w.])-?\d+\.?\d*(?:[eE][-+]?\d+)?")
_TOK = re.compile(r"[A-Za-z_]\w*|-?\d+\.?\d*(?:[eE][-+]?\d+)?|\S")


def normalize_program(src: str) -> list[str]:
    """Lines without comments, whitespace or blank lines, quotes unified and numbers
    rounded to 3 significant digits, so reformatting alone never looks like an edit."""
    out = []
    for line in src.splitlines():
        line = line.split("#", 1)[0]
        line = re.sub(r"\s+", "", line).replace('"', "'")
        line = _NUM.sub(lambda m: f"{float(m.group()):.3g}", line)
        if line:
            out.append(line)
    return out


def _tokens(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        out += _TOK.findall(line) + ["\n"]
    return out


def edit_of(base: list[str], new: list[str]):
    """What `new` changed relative to `base`, at token level (cadrille programs are 4-5 long
    chained lines, so lines are too coarse): (base token slots touched, diff text). A pure
    insertion touches the slot it is inserted at ("+i"); a replaced/deleted token touches i."""
    base, new = _tokens(base), _tokens(new)
    touched, diff = set(), []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=base, b=new, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        touched |= {str(i) for i in range(i1, i2)} if i2 > i1 else {f"+{i1}"}
        diff.append("-" + " ".join(base[i1:i2]) + " +" + " ".join(new[j1:j2]))
    return touched, "\n".join(diff)


def _program(root: Path, r: dict):
    part = (root / "parts" / r["part"]) if (root / "parts").is_dir() else root / r["part"]
    d = part / r["arm"] / (r.get("dir") or f"round_{r['round']:02d}")
    f = d / "program.py"
    return f.read_text() if f.exists() else None


def mark_repeats(root: Path, rows):
    """Tag each proposal (status ok or failed) that repeats an earlier attempt from the same
    program state. Only rejected or failed attempts count; a kept edit starts a new state.
    Sets on the row:
      repeat_eligible  there was at least one earlier failed attempt from this state
      repeat_exact     same normalised program as an earlier attempt
      repeat_near      edit (diff vs the state) >= NEAR similar to an earlier one
      repeat_spot      >= SAME_SPOT of the edited tokens were edited by an earlier attempt (same
                       numbers/calls changed, possibly to other values)
      repeat_rewrite   the proposal rewrote > REWRITE of the program (never a same-spot repeat)
      repeat_of        round of the closest earlier attempt (None if no repeat)"""
    by = defaultdict(list)
    for r in rows:
        by[r["part"], r["arm"]].append(r)
    for (part, arm), rs in by.items():
        rs.sort(key=lambda r: r["round"])
        init = rs[0] if rs and rs[0]["round"] == 0 else None
        src = _program(root, {"part": part, "arm": "init", "round": 0, "dir": "."}) if init else None
        base = normalize_program(src) if src else None
        tried = []                     # (round, program lines, touched, diff) since last keep
        for r in rs[1:]:
            if r.get("status") not in ("ok", "failed"):
                continue
            new_src = _program(root, r)
            if base is None or new_src is None:
                continue
            new = normalize_program(new_src)
            touched, diff = edit_of(base, new)
            n_base = len(_tokens(base))
            rewrite = sum(not t.startswith("+") for t in touched) > REWRITE * n_base
            exact = near = lines = False
            of, best = None, -1.0
            for rnd, prog, t, d in tried:
                sim = difflib.SequenceMatcher(a=d, b=diff, autojunk=False).ratio() if (d or diff) else 1.0
                same = prog == new
                overlap = len(touched & t) / len(touched) if touched and not rewrite else 0.0
                hit = same or sim >= NEAR or overlap >= SAME_SPOT
                exact |= same
                near |= same or sim >= NEAR
                lines |= overlap >= SAME_SPOT
                if hit and max(sim, overlap, float(same)) > best:
                    of, best = rnd, max(sim, overlap, float(same))
            r.update(repeat_eligible=bool(tried), repeat_rewrite=rewrite,
                     repeat_exact=exact, repeat_near=near,
                     repeat_spot=lines, repeat_of=of)
            if r.get("accepted"):
                base, tried = new, []
            else:
                tried.append((r["round"], new, touched, diff))


def repeat_stats(edits):
    elig = [e for e in edits if e.get("repeat_eligible")]
    n = len(elig)
    rate = (lambda k: sum(bool(e.get(k)) for e in elig) / n) if n else (lambda k: None)
    return {"proposals": sum("repeat_eligible" in e for e in edits), "eligible": n,
            "exact": rate("repeat_exact"), "near": rate("repeat_near"),
            "same_spot": rate("repeat_spot"), "rewrites": rate("repeat_rewrite"),
            "any": None if not n else sum(e.get("repeat_of") is not None for e in elig) / n}


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


def run_prices(root: Path) -> dict | None:
    """USD prices for a run: the ones frozen in config.json when it started, else the
    current .env prices (Vertex runs only; local backends cost nothing to report)."""
    f = root / "config.json"
    cfg = json.loads(f.read_text()) if f.exists() else {}
    if cfg.get("prices"):
        return cfg["prices"]
    return vertex_ai.prices() if cfg.get("backend", "vertex") == "vertex" else None


def summarize(root: Path) -> dict:
    rows, finals = load(root)
    mark_repeats(root, rows)
    prices = run_prices(root)
    for d in finals.values():
        d["cost_usd"] = vertex_ai.cost_usd(d.get("prompt_tokens"), d.get("output_tokens"), prices)
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
            "repeats": repeat_stats(edits),
            "kernel_warnings_per_edit": mean([e.get("kernel_warnings") for e in valid]),
            "tokens_per_part": mean([f.get("prompt_tokens", 0) + f.get("output_tokens", 0) for f in fin.values()]),
            "cost_per_part": mean([f.get("cost_usd") for f in fin.values()]),
            "cost_total": None if prices is None else sum(f.get("cost_usd") or 0 for f in fin.values()),
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
            "cost_usd", "wall_seconds"]
    init = {(r["part"], r["arm"]): r for r in rows if r["round"] == 0}
    with open(root / "parts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys + ["iou3d_init", "iou3d_best_oracle"])
        for (p, a), d in sorted(finals.items()):
            w.writerow([d.get(k) for k in keys] + [init.get((p, a), {}).get("iou3d"),
                                                   d.get("best_oracle", {}).get("iou3d")])
    ekeys = ["part", "arm", "round", "status", "accepted", "verdict", "geo_decision", "vlm_decision",
             "geo_gain", "geo_inconclusive", "change_tag", "iou3d_before", "iou3d", "w_iou",
             "qa_yes", "qa_n", "kernel_warnings", "repairs_used", "wall_seconds",
             "repeat_eligible", "repeat_rewrite", "repeat_exact", "repeat_near", "repeat_spot",
             "repeat_of"]
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
        rp = m["repeats"]
        if rp["eligible"]:
            print(f"  repeats: {rp['eligible']} proposals after a failed attempt from the same "
                  f"program; exact {f(rp['exact'], 2)}, near {f(rp['near'], 2)}, "
                  f"same spot {f(rp['same_spot'], 2)}, any {f(rp['any'], 2)} "
                  f"(rewrites, never counted as same spot: {f(rp['rewrites'], 2)})")
        if m["cost_total"] is not None:
            print(f"  cost: ${m['cost_total']:.2f} total, ${m['cost_per_part']:.3f} per part")


if __name__ == "__main__":
    main()
