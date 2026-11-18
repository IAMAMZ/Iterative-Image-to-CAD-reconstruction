"""Turn cadrille's predicted programs into refine.py starting programs.

    uv run python cadrille_init.py split                      # -> data/fusion360/stage1.txt
    uv run python data/fusion360_targets.py                   # build the targets of that split
    uv run python cadrille_init.py convert --tag rl           # -> data/generated/init/cadrille_rl/<part>.py
    uv run python refine.py data/generated/targets/fusion360/* --init data/generated/init/cadrille_rl ...

    uv run python cadrille_init.py tune                       # -> data/fusion360/tuning.txt

convert
  * appends `result = r` (cadrille assigns its solid to `r`)
  * placement (as in GATOR's placement step): fits one isotropic scale of the solid to the
    target's silhouettes and depth maps by rendering it with the target's cameras, keeping
    the orientation and the shape. The fitted scale is appended as visible code, so the
    agent sees it and can keep or change it. Uses only the target views, never the GT.
    Disable with --no-placement (ablation).
  * copies cadrille's own scores (cadrille protocol: bbox-normalised IoU / CD) to
    scores.json, and logs parts whose cadrille program does not build (invalid rate, IR).

tune
  a small tuning set (default 3 per IoU bin) with the same strata, drawn only from test parts
  outside the Stage 1 split -> data/fusion360/tuning.txt. Pilots and prompt changes use these
  parts, so the 60 evaluation parts stay unseen until the final run.

split
  ~60 parts of the Fusion360 test split, stratified by cadrille-RL IoU (< 0.6, 0.6-0.9,
  >= 0.9) and, inside each bin, by mesh complexity (faces + vertices of the GT mesh, median
  split, as CADPrompt does). Writes the list plus stage1_meta.json with each part's strata.
"""
import argparse
import json
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

import layout
import sandbox
from view_weights import measure_bbox, view_weights

ROOT = Path(__file__).parent
CADRILLE = ROOT / "cadrille"
GT_DIR = CADRILLE / "results" / "fusion360_test_gt"
SPLITS = ROOT / "data" / "fusion360"          # <dataset>/<split> layout
TARGETS = ROOT / "data" / "generated" / "targets" / "fusion360"
SEED = 2529
IOU_BINS = ((0.0, 0.6, "low"), (0.6, 0.9, "mid"), (0.9, 1.01, "high"))
PLACEMENT_MARK = "# placement:"


# ------------------------------------------------------------------ program text
def to_refine_program(src: str) -> str:
    """cadrille program (solid in `r`) -> program that defines `result`."""
    src = src.rstrip() + "\n"
    if "import cadquery as cq" not in src:
        src = "import cadquery as cq\n" + src
    return src + "result = r\n"


def placement_code(scale: float) -> str:
    return (f"{PLACEMENT_MARK} isotropic scale fitted to the target views "
            f"(orientation unchanged)\nresult = cq.Workplane(obj=result.val().scale({scale:.4f}))\n")


# ------------------------------------------------------------------ placement
def _render_metrics(mesh, target_dir, rig, renderer, norm, center, target_views):
    """Render `mesh` (target units) centred at `center` in the target frame -> compare report."""
    from compare import view_metrics
    from rig import normalize, render_rig
    m = mesh.copy()
    m.apply_translation(np.asarray(center) - m.bounding_box.centroid)
    mn, _, _ = normalize(m, norm["center"], norm["scale"])
    views = render_rig(renderer, mn, rig)
    return {"views": {v: view_metrics(target_views[v][0], target_views[v][1],
                                      views[v][2].astype(bool), views[v][1])
                      for v in target_views}}


def fit_scale(mesh, target_dir: Path, rig: dict, weights=None, lo=0.7, hi=1.4, iters=10):
    """Isotropic scale s maximising the weighted geometric score. -> (s, score(s), score(1))"""
    from compare import load_views
    from cq_render import CQRenderer
    from geo_check import geo_score
    tv, tinfo = load_views(target_dir)
    norm = tinfo["normalization"]
    blo, bhi = measure_bbox(target_dir, rig)
    center = (blo + bhi) / 2
    cache = {}
    with CQRenderer(rig["width"], rig["height"]) as r:
        def f(s):
            s = round(float(s), 4)
            if s not in cache:
                m = mesh.copy()
                m.apply_scale(s)
                cache[s] = geo_score(_render_metrics(m, target_dir, rig, r, norm, center, tv),
                                     weights)
            return cache[s]
        grid = np.exp(np.linspace(math.log(lo), math.log(hi), 13))
        best = max(grid, key=f)
        step = grid[1] / grid[0]
        a, b = best / step, best * step               # golden-section search around it
        g = (math.sqrt(5) - 1) / 2
        for _ in range(iters):
            c, d = b - g * (b - a), a + g * (b - a)
            if f(c) > f(d):
                b = d
            else:
                a = c
        s = max([best, (a + b) / 2], key=f)
        return float(round(s, 4)), f(s), f(1.0)


# ------------------------------------------------------------------ commands
def build_mesh(src: str, work: Path, sandboxed=False):
    """Run a program through generate_solid.py (crash safe; optionally in the bwrap sandbox,
    see sandbox.py) -> trimesh or error text."""
    work.mkdir(parents=True, exist_ok=True)
    (work / "program.py").write_text(src)
    cmd = [sys.executable, str(ROOT / "generate_solid.py"), str(work / "program.py"),
           "--out", str(work)]
    if sandboxed:
        cmd = sandbox.wrap(cmd, writable=[work])
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        return None, "\n".join(p.stderr.strip().splitlines()[-6:]) or f"exit {p.returncode}"
    return trimesh.load(work / "solid.stl", force="mesh"), None


def convert(args):
    from rig import load_rig
    src_dir = CADRILLE / "work_dirs" / f"f360_{args.tag}" / "py"
    if not src_dir.is_dir():          # SFT outputs were moved to the git-ignored archive/
        raise SystemExit(f"{src_dir} not found: only the RL outputs are in the repo "
                         "(SFT is archived, see archive/MANIFEST.jsonl); use --tag rl")
    out = args.out or ROOT / "data" / "generated" / "init" / f"cadrille_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    scores = {r["id"]: r for r in json.loads(
        (CADRILLE / "work_dirs" / f"f360_{args.tag}" / "scores.json").read_text())}
    parts = [p.name for p in sorted(args.targets.iterdir()) if layout.info(p).exists()]
    parts = parts[:args.limit]
    rig = load_rig()
    log = {"tag": args.tag, "placement": not args.no_placement, "parts": {}}
    for part in parts:
        rec = {"cadrille": scores.get(part)}
        f = src_dir / f"{part}.py"
        if not f.exists():
            rec["error"] = "no cadrille program"
        else:
            src = to_refine_program(f.read_text())
            mesh, err = build_mesh(src, out / "_work" / part, args.sandbox)
            if err:
                rec["error"] = err             # invalid cadrille program (counts towards IR)
            else:
                if not args.no_placement:
                    w = view_weights(args.targets / part, rig)
                    s, fs, f1 = fit_scale(mesh, args.targets / part, rig, w)
                    apply = abs(s - 1) > 0.005 and fs > f1 + 1e-3
                    rec.update(fitted_scale=s, scale=s if apply else 1.0,
                               score_fitted=fs, score_unscaled=f1)
                    if apply:
                        src += placement_code(s)
                (out / f"{part}.py").write_text(src)
            shutil.rmtree(out / "_work" / part, ignore_errors=True)
        log["parts"][part] = rec
        msg = rec.get("error", "").splitlines()[-1:] if "error" in rec else \
            [f"ok, scale {rec.get('scale', 1.0):.3f}"]
        print(f"{part}: {msg[0] if msg else 'failed'}", flush=True)
    shutil.rmtree(out / "_work", ignore_errors=True)
    (out / "init_log.json").write_text(json.dumps(log, indent=1))
    (out / "scores.json").write_text(json.dumps(
        {p: r["cadrille"] for p, r in log["parts"].items() if r.get("cadrille")}, indent=1))
    bad = [p for p, r in log["parts"].items() if "error" in r]
    print(f"{len(parts) - len(bad)}/{len(parts)} starting programs in {out} "
          f"({len(bad)} invalid: {bad[:5]}{'...' if len(bad) > 5 else ''})")


def split(args, out_name="stage1", exclude=(), seed=SEED):
    """Stratified subset of the test parts -> data/fusion360/<name>.txt + <name>_meta.json."""
    scores = {r["id"]: r for r in json.loads(
        (CADRILLE / "work_dirs" / "f360_rl" / "scores.json").read_text())}
    test = [l.strip() for l in (SPLITS / "test" / "ids.txt").read_text().split() if l.strip()]
    rows = []
    for p in test:
        if p in exclude:
            continue
        r = scores.get(p)
        if not r or not r.get("valid") or r.get("iou") is None or not (GT_DIR / f"{p}.stl").exists():
            continue
        m = trimesh.load_mesh(GT_DIR / f"{p}.stl")
        rows.append({"part": p, "cadrille_rl_iou": r["iou"], "cadrille_rl_cd": r["cd_x1000"],
                     "complexity": int(len(m.faces) + len(m.vertices))})
    med = float(np.median([r["complexity"] for r in rows]))
    rng = random.Random(seed)
    chosen = []
    for lo, hi, name in IOU_BINS:
        pool = [dict(r, iou_bin=name, mesh=("complex" if r["complexity"] > med else "simple"))
                for r in rows if lo <= r["cadrille_rl_iou"] < hi]
        per = args.per_bin
        halves = [[r for r in pool if r["mesh"] == k] for k in ("simple", "complex")]
        for h in halves:
            rng.shuffle(h)
        take = halves[0][:per // 2] + halves[1][:per - per // 2]
        rest = [r for h in halves for r in h if r not in take]
        take += rest[:per - len(take)]                 # top up if one half is short
        chosen += take
    chosen.sort(key=lambda r: r["part"])
    (SPLITS / f"{out_name}.txt").write_text("\n".join(r["part"] for r in chosen) + "\n")
    meta = {"seed": seed, "per_bin": args.per_bin, "complexity_median": med,
            "iou_bins": IOU_BINS, "parts": {r.pop("part"): r for r in chosen}}
    if exclude:
        meta["excluded"] = f"{len(exclude)} parts of the evaluation split"
    (SPLITS / f"{out_name}_meta.json").write_text(json.dumps(meta, indent=1))
    print(f"wrote {len(chosen)} parts to {SPLITS / (out_name + '.txt')}")


def tune(args):
    """Tuning set for pilots and prompt changes: same strata as Stage 1, drawn only from
    test parts that are NOT in the Stage 1 evaluation split, so the evaluation parts stay
    unseen while the method is developed."""
    stage1 = SPLITS / "stage1.txt"
    if not stage1.exists():
        raise SystemExit("run `cadrille_init.py split` first: the tuning set excludes its parts")
    exclude = set(stage1.read_text().split())
    split(args, out_name="tuning", exclude=exclude, seed=SEED + 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--per-bin", type=int, default=20)
    t = sub.add_parser("tune", help="tuning set outside the Stage 1 parts (for pilots)")
    t.add_argument("--per-bin", type=int, default=3)
    c = sub.add_parser("convert")
    c.add_argument("--tag", default="rl", choices=["rl", "sft"])
    c.add_argument("--targets", type=Path, default=TARGETS)
    c.add_argument("--out", type=Path, default=None)
    c.add_argument("--limit", type=int, default=None)
    c.add_argument("--no-placement", action="store_true")
    c.add_argument("--sandbox", action="store_true",
                   help="build the programs inside a bubblewrap sandbox (Linux only)")
    args = ap.parse_args()
    if getattr(args, "sandbox", False):
        try:
            sandbox.check()
        except sandbox.SandboxUnavailable as e:
            ap.error(str(e))
    {"split": split, "tune": tune, "convert": convert}[args.cmd](args)


if __name__ == "__main__":
    main()
