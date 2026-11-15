"""Summarise refine.py runs: VLM visual review vs forward-rendering geometric check.

    uv run python summarize_runs.py out/refine            # prints a table, writes summary.json

Per arm:
  * 3D IoU / Chamfer of the first program and of the final kept program (vs hidden solid)
  * edit acceptance against what the edit really did to the hidden 3D shape:
      kept-good   accepted and the 3D IoU went up      (want high)
      kept-bad    accepted and the 3D IoU went down    (want low)
      dropped-good rejected though it would have helped
      dropped-bad  rejected and it would have hurt     (want high)
  * invalid proposals (never built a solid even after repairs) and model time
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


def summarize(root: Path) -> dict:
    rows = [json.loads(l) for f in sorted(root.glob("*/*/results.jsonl"))
            for l in f.read_text().splitlines()]
    by_arm = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    out = {}
    for arm, rs in sorted(by_arm.items()):
        parts = sorted({r["part"] for r in rs})
        init = {r["part"]: r for r in rs if r["round"] == 0}
        final = {p: json.loads((root / p / arm / "final.json").read_text())
                 for p in parts if (root / p / arm / "final.json").exists()}
        edits = [r for r in rs if r["round"] > 0]
        c = defaultdict(int)
        for e in edits:
            if not e["valid"]:
                c["invalid"] += 1
                continue
            good = {"beneficial": "good", "harmful": "bad"}.get(e.get("verdict"), "neutral")
            c[("kept-" if e["accepted"] else "dropped-") + good] += 1
        kept = c["kept-good"] + c["kept-bad"] + c["kept-neutral"]
        out[arm] = {
            "parts": len(parts), "edits": len(edits),
            "init_iou3d": mean(r.get("iou3d") for r in init.values()),
            "final_iou3d": mean(f.get("iou3d") for f in final.values()),
            "init_chamfer": mean(r.get("chamfer_x1000") for r in init.values()),
            "final_chamfer": mean(f.get("chamfer_x1000") for f in final.values()),
            "final_mean_sil_iou": mean(f.get("mean_iou") for f in final.values()),
            "acceptance": dict(c),
            "kept_precision": c["kept-good"] / kept if kept else None,
            "model_seconds": round(sum(e.get("llm_seconds", 0) for e in edits), 1),
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", type=Path, help="refine.py --out dir")
    args = ap.parse_args()
    s = summarize(args.root)
    (args.root / "summary.json").write_text(json.dumps(s, indent=2) + "\n")
    f = lambda x, p=3: "n/a" if x is None else f"{x:.{p}f}"
    for arm, m in s.items():
        a = m["acceptance"]
        print(f"[{arm}] {m['parts']} parts, {m['edits']} edits, {m['model_seconds']:.0f}s of model time")
        print(f"  3D IoU   first {f(m['init_iou3d'])} -> final {f(m['final_iou3d'])}")
        print(f"  Chamfer  first {f(m['init_chamfer'], 2)} -> final {f(m['final_chamfer'], 2)}  (x1000, lower is better)")
        print(f"  kept:    good {a.get('kept-good', 0)}, bad {a.get('kept-bad', 0)}, neutral {a.get('kept-neutral', 0)}"
              f"   (share of kept edits that helped: {f(m['kept_precision'], 2)})")
        print(f"  dropped: good {a.get('dropped-good', 0)}, bad {a.get('dropped-bad', 0)}, neutral {a.get('dropped-neutral', 0)}"
              f"   invalid {a.get('invalid', 0)}")


if __name__ == "__main__":
    main()
