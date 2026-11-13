"""Iterative image-to-CAD refinement: a VLM agent edits a CadQuery program round by round.

Two ways to decide whether an edit is kept (the two arms of the Stage 1 comparison):
  vlm  VLM visual review: the agent sees target and candidate renders, and the VLM
       itself judges whether the new version is closer (KEEP A / KEEP B).
  geo  forward-rendering geometric check: the agent also gets the silhouette / depth
       residual images and per-view numbers, and an edit is kept only if it builds a
       valid solid and improves silhouette + depth agreement without making any view
       much worse.

Both arms start from the same first program per part, so they are directly comparable.
The hidden true solid is used only offline (eval3d.py) to score what each arm kept.

    ollama serve &                                       # local VLM, no API key
    uv run python part_generators.py --n 2 --out out/pilot
    uv run python refine.py out/pilot/* --arm both --rounds 4 --out out/refine
    uv run python summarize_runs.py out/refine

Targets are generate_solid.py output dirs (renders + depth.npz + info.json). The agent
reads only the renders and depth maps; solid.step and part.py are for evaluation only.
"""
import argparse
import io
import json
import random
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import vlm
from compare import compare
from eval3d import evaluate
from rig import load_rig

ROOT = Path(__file__).parent
GRID_VIEWS = ("front", "right", "top", "iso_fr")
BUILD_TIMEOUT = 180  # seconds; model-written code can be pathological


# ------------------------------------------------------------------ observations
def measure_bbox(target_dir: Path, rig: dict):
    """Bounding box (mm) of the target from its depth maps and the calibrated cameras:
    back-project every foreground pixel of every view to 3D. Uses no 3D model."""
    info = json.loads((target_dir / "info.json").read_text())
    center = np.array(info["normalization"]["center"])
    scale = info["normalization"]["scale"]
    depth = np.load(target_dir / "depth.npz")
    K = np.array(rig["K"])
    pts = []
    for cam in rig["cameras"]:
        d = depth[cam["name"]]
        v, u = np.nonzero(d > 0)
        z = d[v, u]
        x = (u + 0.5 - K[0, 2]) / K[0, 0] * z
        y = -(v + 0.5 - K[1, 2]) / K[1, 1] * z          # image down -> camera -y (OpenGL)
        P = np.array(cam["pose_c2w"])
        with np.errstate(all="ignore"):  # spurious matmul warnings from macOS Accelerate
            pts.append(np.stack([x, y, -z], 1).astype(np.float64) @ P[:3, :3].T + P[:3, 3])
    pts = np.concatenate(pts) / scale + center              # normalised units -> mm
    return pts.min(0), pts.max(0)


def grid(paths, labels, tile=256) -> bytes:
    """2x2 labelled grid of images -> PNG bytes."""
    sheet = Image.new("RGB", (2 * tile, 2 * tile), (255, 255, 255))
    for i, (p, lab) in enumerate(zip(paths, labels)):
        im = Image.open(p).convert("RGB").resize((tile, tile), Image.LANCZOS)
        ImageDraw.Draw(im).text((6, 5), lab, fill=(0, 0, 0))
        sheet.paste(im, ((i % 2) * tile, (i // 2) * tile))
    buf = io.BytesIO()
    sheet.save(buf, "PNG")
    return buf.getvalue()


def render_grid(d: Path, suffix="", labels=None):
    return grid([d / f"{v}{suffix}.png" for v in GRID_VIEWS], labels or list(GRID_VIEWS))


def residual_table(report):
    rows = [f"{'view':8s} {'IoU':>5s} {'missing px':>10s} {'extra px':>9s} {'depth MAE mm':>12s}"]
    for v, m in report["views"].items():
        d = "n/a" if m["depth_mae_mm"] is None else f"{m['depth_mae_mm']:.2f}"
        rows.append(f"{v:8s} {m['iou']:5.3f} {m['missing_px']:10d} {m['extra_px']:9d} {d:>12s}")
    return "\n".join(rows)


# ------------------------------------------------------------------ build + score
def build(src: str, cand_dir: Path, target_dir: Path, center):
    """Run a program in a subprocess (crash/timeout safe). -> error text or None."""
    cand_dir.mkdir(parents=True, exist_ok=True)
    (cand_dir / "program.py").write_text(src)
    bad = vlm.check_code(src)
    if bad:
        return bad
    cmd = [sys.executable, str(ROOT / "generate_solid.py"), str(cand_dir / "program.py"),
           "--out", str(cand_dir), "--like", str(target_dir),
           "--center-at", *[f"{c:.6f}" for c in center]]
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"the program took longer than {BUILD_TIMEOUT}s to build; simplify it"
    if p.returncode != 0:
        err = "\n".join(l for l in p.stderr.splitlines() if not l.startswith("FAILED, see"))
        return err.strip()[-1500:] or f"build failed (exit {p.returncode})"
    return None


def score(target_dir: Path, cand_dir: Path):
    report = compare(target_dir, cand_dir, cand_dir / "compare")
    try:
        e3d = evaluate(target_dir, cand_dir)
    except Exception as e:  # never let offline scoring kill a run
        e3d = {"iou3d": None, "chamfer_x1000": None, "error": f"{type(e).__name__}: {e}"}
    info = json.loads((cand_dir / "info.json").read_text())
    size = (np.array(info["bbox_max"]) - np.array(info["bbox_min"])).tolist()
    return {"dir": cand_dir, "report": report, "e3d": e3d, "size": size,
            "src": (cand_dir / "program.py").read_text()}


def geo_score(report, depth_weight=1.0):
    d = report["mean_depth_mae"]
    return report["mean_iou"] - depth_weight * (1.0 if d is None else d)


def geo_accept(cur, new, min_gain=1e-3, max_view_drop=0.05):
    """Keep an edit only if the combined silhouette+depth score improves and no single
    view's silhouette IoU gets worse by more than max_view_drop."""
    gain = geo_score(new) - geo_score(cur)
    drop = min(new["views"][v]["iou"] - cur["views"][v]["iou"] for v in cur["views"])
    return gain > min_gain and drop >= -max_view_drop, {"gain": gain, "worst_view_drop": drop}


# ------------------------------------------------------------------ agent steps
class Agent:
    def __init__(self, model, think, repairs):
        self.model, self.think, self.repairs = model, think, repairs
        self.llm_seconds = 0.0
        self.calls = 0

    def ask(self, messages):
        text, st = vlm.chat(messages, self.model, self.think)
        self.llm_seconds += st["seconds"]
        self.calls += 1
        return text, st

    def write_program(self, user_msg, images, cand_dir, target_dir, center):
        """Ask for a program; on build errors feed the error back up to `repairs` times.
        -> (ok, attempts, transcript)"""
        messages = [{"role": "system", "content": vlm.SYSTEM},
                    {"role": "user", "content": user_msg, "images": images}]
        transcript = []
        for attempt in range(1, self.repairs + 2):
            text, st = self.ask(messages)
            transcript.append({"attempt": attempt, "reply": text, **st})
            src = vlm.extract_code(text)
            err = "the reply had no ```python code block" if src is None else \
                build(src, cand_dir, target_dir, center)
            transcript[-1]["error"] = err
            if err is None:
                return True, attempt, transcript
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": vlm.repair_prompt(err)}]
        return False, attempt, transcript

    def judge(self, target_img, cur_img, new_img, rng):
        """VLM visual review. Randomises which side is A to avoid position bias.
        -> (keep_new, reply)"""
        new_is_b = rng.random() < 0.5
        a, b = (cur_img, new_img) if new_is_b else (new_img, cur_img)
        prompt = vlm.VLM_JUDGE.format(views=vlm.VIEWS_TEXT)
        text, _ = self.ask([{"role": "user", "content": prompt, "images": [target_img, a, b]}])
        pick = vlm.parse_judgement(text)
        keep_new = pick == ("B" if new_is_b else "A")
        return keep_new, {"reply": text, "pick": pick, "new_was": "B" if new_is_b else "A"}


# ------------------------------------------------------------------ runs
def initial(agent, target_dir, out, lo, hi, center, target_img):
    """First program for a part, shared by both arms (cached on disk)."""
    d = out / "init"
    if (d / "info.json").exists() and (d / "init.json").exists():
        return json.loads((d / "init.json").read_text())["ok"]
    ok, attempts, tr = agent.write_program(vlm.initial_prompt(lo, hi), [target_img], d,
                                           target_dir, center)
    (d / "init.json").write_text(json.dumps({"ok": ok, "attempts": attempts,
                                             "transcript": tr}, indent=2))
    return ok


def refine_part(agent, arm, target_dir, part_out, rounds, lo, hi, center, target_img, seed):
    rng = random.Random(seed)
    run_dir = part_out / arm
    run_dir.mkdir(parents=True, exist_ok=True)
    results = run_dir / "results.jsonl"
    results.unlink(missing_ok=True)

    def log(row):
        row = {"part": target_dir.name, "arm": arm, **row}
        with results.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(f"  [{arm}] round {row['round']}: " + ", ".join(
            f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
            for k, v in row.items() if k in ("valid", "accepted", "mean_iou", "iou3d", "verdict")),
            flush=True)

    cur = score(target_dir, part_out / "init")
    log({"round": 0, "valid": True, "accepted": True, "mean_iou": cur["report"]["mean_iou"],
         "depth_mae": cur["report"]["mean_depth_mae"], **cur["e3d"]})
    for r in range(1, rounds + 1):
        rd = run_dir / f"round_{r:02d}"
        cur_img = render_grid(cur["dir"])
        images = [target_img, cur_img]
        table = None
        if arm == "geo":
            images += [render_grid(cur["dir"] / "compare", "_overlay",
                                   [f"{v}  IoU {cur['report']['views'][v]['iou']:.3f}"
                                    for v in GRID_VIEWS]),
                       render_grid(cur["dir"] / "compare", "_depth_err")]
            table = residual_table(cur["report"])
        msg = vlm.refine_prompt(arm, cur["src"], lo, hi, cur["size"], table)
        t0 = agent.llm_seconds
        ok, attempts, tr = agent.write_program(msg, images, rd, target_dir, center)
        row = {"round": r, "valid": ok, "attempts": attempts}
        decision = {}
        if ok:
            new = score(target_dir, rd)
            if arm == "geo":
                keep, decision = geo_accept(cur["report"], new["report"])
            else:
                keep, decision = agent.judge(target_img, cur_img, render_grid(rd), rng)
            # offline only: did this edit actually help the hidden 3D shape?
            a, b = cur["e3d"]["iou3d"], new["e3d"]["iou3d"]
            verdict = None if a is None or b is None else \
                "beneficial" if b > a + 0.005 else "harmful" if b < a - 0.005 else "neutral"
            row.update(accepted=keep, verdict=verdict, mean_iou=new["report"]["mean_iou"],
                       depth_mae=new["report"]["mean_depth_mae"], **new["e3d"],
                       iou3d_before=a)
            if keep:
                cur = new
        else:
            row.update(accepted=False, verdict=None)
        row["llm_seconds"] = round(agent.llm_seconds - t0, 1)
        (rd / "agent.json").write_text(json.dumps({"transcript": tr, "decision": decision},
                                                  indent=2, default=str))
        log(row)
    final = {"part": target_dir.name, "arm": arm, "final_dir": str(cur["dir"]),
             "mean_iou": cur["report"]["mean_iou"], **cur["e3d"]}
    (run_dir / "final.json").write_text(json.dumps(final, indent=2))
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", type=Path, nargs="+", help="generate_solid.py output dirs")
    ap.add_argument("--arm", choices=["vlm", "geo", "both"], default="both")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--repairs", type=int, default=2, help="retries after a build error")
    ap.add_argument("--model", default="gemma4:12b")
    ap.add_argument("--think", action="store_true", help="let the model think (slower)")
    ap.add_argument("--init", type=Path, default=None,
                    help="dir of <part>.py starting programs (e.g. from cadrille) instead of "
                         "asking the VLM for the first program")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("out/refine"))
    args = ap.parse_args()

    rig = load_rig()
    arms = ["vlm", "geo"] if args.arm == "both" else [args.arm]
    targets = [t for t in args.targets if (t / "depth.npz").exists()]
    for target in targets:
        part_out = args.out / target.name
        part_out.mkdir(parents=True, exist_ok=True)
        lo, hi = measure_bbox(target, rig)
        center = (lo + hi) / 2
        target_img = render_grid(target)
        agent = Agent(args.model, args.think, args.repairs)
        print(f"{target.name}: measured bbox {np.round(hi - lo, 1).tolist()} mm", flush=True)
        try:
            if args.init:
                err = build((args.init / f"{target.name}.py").read_text(), part_out / "init",
                            target, center)
                ok = err is None
                (part_out / "init" / "init.json").write_text(json.dumps({"ok": ok, "error": err}))
            else:
                ok = initial(agent, target, part_out, lo, hi, center, target_img)
            if not ok:
                print("  no valid first program; skipping part", flush=True)
                continue
            for i, arm in enumerate(arms):
                refine_part(agent, arm, target, part_out, args.rounds, lo, hi, center,
                            target_img, args.seed + i)
        except Exception:
            traceback.print_exc()
            print(f"  {target.name} crashed; continuing with the next part", flush=True)


if __name__ == "__main__":
    main()
