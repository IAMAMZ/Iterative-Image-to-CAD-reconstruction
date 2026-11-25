"""Iterative image-to-CAD refinement: a VLM agent edits a CadQuery program round by round.

Every arm starts from the same first program per part (cadrille's prediction, after the
placement fit, or one the agent writes itself), and every arm gets the CAD-kernel report
of the current program. Arms differ in what else the agent sees and in who decides
whether an edit is kept:

  arm       agent sees                                     edit kept if
  premise   target + candidate renders                     the VLM judge prefers it
            (3D-Premise-style baseline)
  vlm       + failed verification questions (CADCodeVerify-style visual review)
                                                           the VLM judge prefers it
  geo       + silhouette/depth residual images, a zoom on   the weighted forward-rendering
  (main     the largest residual, per-view table with        check passes (geo_check.py)
  method)
            view weights
  hybrid    everything geo and vlm see                     the check passes AND the judge
            (ablation: geo + CADCodeVerify-style review)   prefers it; if the check is
                                                           inconclusive, the judge decides
  oracle    as geo                                         the hidden 3D IoU goes up
            (analysis only: upper bound of a gate)
  gsolver   as vlm + GT-vs-candidate geometric properties  always (CADCodeVerify protocol)
            (analysis only: CADCodeVerify's geometric-solver* upper bound; uses the GT)

Every round logs the decision of the geometric check for every arm ("shadow" decision),
the judge's decision where it ran, and what the edit really did to the hidden 3D shape,
so the review methods can be compared on the same edits. A run stops after --rounds,
when --budget-seconds is used up, when the agent replies NO_CHANGE, or (question arms)
when every verification question is answered "Yes".

    uv run python cadrille_init.py split && uv run python data/fusion360_targets.py
    uv run python cadrille_init.py convert --tag rl
    uv run python refine.py data/generated/targets/fusion360/* \
        --init data/generated/init/cadrille_rl --arm all --rounds 4 --name stage1
    # -> runs/<date>_stage1/: open README.md there (written as the run goes; see report.py)

--backend vertex (default) uses Gemini on Vertex AI, configured in .env (see .env.example);
--backend ollama uses the local model. Use --backend echo for a dry run without any model.
Targets are rendered-solid folders (layout.py; data/fusion360_targets.py or generate_solid.py).
The agent reads only the renders and depth maps; gt.stl / solid.step are for offline scoring
only. Run folder layout: see report.py (and the README.md it writes into every run).
"""
import argparse
import datetime
import difflib
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

import vertex_ai
import vlm
from compare import compare, largest_residual, load_views, write_effect_images
from eval3d import evaluate, properties
from geo_check import (SIGNALS, edit_delta, geo_accept, geo_score, residual_table, restrict,
                       weighted_means)
import layout
import progress
import report
import sandbox
from rig import load_rig
from summarize_runs import normalize_program
from view_weights import measure_bbox, view_weights

ROOT = Path(__file__).parent
RUNS = ROOT / "runs"          # default home of run folders (git-ignored)
GRID_VIEWS = layout.grid_views()   # the 4 rig cameras, 2x2 grid order
BUILD_TIMEOUT = 180  # seconds; model-written code can be pathological
BENEFIT = 0.005      # 3D IoU change that counts as a real improvement / harm (offline label)
TEMPERATURE = 1.0    # Gemini 3's recommended setting
ALL_YES_IOU = 0.98   # arms with geometric evidence only stop on "all questions Yes" when the
                     # weighted silhouette IoU is already this good
FB_ATTEMPTS = 3      # edit feedback: attempts shown (since the last kept edit)
FB_HISTORY = 8       # edit feedback: round-history lines shown
FB_DIFF_LINES = 30   # edit feedback: diff lines per attempt

# what each arm shows the agent and how it decides; see the module docstring
ARMS = {
    "premise": {"residuals": False, "qa": False, "gsolver": False, "accept": "judge"},
    "vlm":     {"residuals": False, "qa": True,  "gsolver": False, "accept": "judge"},
    "geo":     {"residuals": True,  "qa": False, "gsolver": False, "accept": "geo"},
    "hybrid":  {"residuals": True,  "qa": True,  "gsolver": False, "accept": "hybrid"},
    "oracle":  {"residuals": True,  "qa": False, "gsolver": False, "accept": "oracle"},
    "gsolver": {"residuals": False, "qa": True,  "gsolver": True,  "accept": "always"},
}
MAIN_ARMS = ("premise", "vlm", "geo", "hybrid")


# ------------------------------------------------------------------ images
def _png(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def grid(paths, labels, tile=256) -> bytes:
    """2x2 labelled grid of images -> PNG bytes. A single image fills the whole sheet
    (one-view ablation), so it is shown at the same size as the grid."""
    if len(paths) == 1:
        tile *= 2
    sheet = Image.new("RGB", (tile, tile) if len(paths) == 1 else (2 * tile, 2 * tile),
                      (255, 255, 255))
    for i, (p, lab) in enumerate(zip(paths, labels)):
        im = Image.open(p).convert("RGB").resize((tile, tile), Image.LANCZOS)
        ImageDraw.Draw(im).text((6, 5), lab, fill=(0, 0, 0))
        sheet.paste(im, ((i % 2) * tile, (i // 2) * tile))
    return _png(sheet)


def render_grid(d: Path, labels=None, views=None):
    views = views or GRID_VIEWS
    return grid([layout.render(d, v) for v in views], labels or list(views))


def diff_grid(d: Path, kind, labels=None, views=None):
    """kind: "_overlay" or "_depth_err" (compare.py's images of candidate dir d)."""
    views = views or GRID_VIEWS
    return grid([layout.diff(d, v, kind) for v in views], labels or list(views))


def detail_strip(target_dir: Path, cand_dir: Path, weights=None, tile=256, margin=24,
                 views=None, kind="_overlay"):
    """Zoom on the largest residual blob over the views (GATOR's detail view):
    target | candidate | residual (kind "_overlay") or depth error ("_depth_err").
    -> (png bytes, view) or (None, None)."""
    tv, _ = load_views(target_dir)
    cv, _ = load_views(cand_dir)
    best = (0, None, None)
    for v in (views or tv):
        area, box = largest_residual(tv[v][0], cv[v][0])
        area *= 1.0 if weights is None else float(weights.get(v, 1.0))
        if box and area > best[0]:
            best = (area, v, box)
    _, v, box = best
    if v is None:
        return None, None
    r0, r1, c0, c1 = box
    h, w = tv[v][0].shape
    side = max(r1 - r0, c1 - c0) + 2 * margin
    cy, cx = (r0 + r1) // 2, (c0 + c1) // 2
    top, left = int(np.clip(cy - side // 2, 0, max(h - side, 0))), int(np.clip(cx - side // 2, 0, max(w - side, 0)))
    crop = (left, top, min(left + side, w), min(top + side, h))
    srcs = [(layout.render(target_dir, v), "target"), (layout.render(cand_dir, v), "current"),
            (layout.diff(cand_dir, v, kind), "residual" if kind == "_overlay" else "depth error")]
    sheet = Image.new("RGB", (3 * tile, tile), (255, 255, 255))
    for i, (p, lab) in enumerate(srcs):
        im = Image.open(p).convert("RGB").crop(crop).resize((tile, tile), Image.NEAREST)
        ImageDraw.Draw(im).text((6, 5), f"{v} zoom: {lab}", fill=(0, 0, 0))
        sheet.paste(im, (i * tile, 0))
    return _png(sheet), v


# ------------------------------------------------------------------ build + score
def build(src: str, cand_dir: Path, target_dir: Path, center, sandboxed=False):
    """Run a program in a subprocess (crash/timeout safe), optionally inside the bwrap
    sandbox (sandbox.py; Linux only). -> error text or None."""
    cand_dir.mkdir(parents=True, exist_ok=True)
    (cand_dir / "program.py").write_text(src)
    bad = vlm.check_code(src)
    if bad:
        return bad
    cmd = [sys.executable, str(ROOT / "generate_solid.py"), str(cand_dir / "program.py"),
           "--out", str(cand_dir), "--like", str(target_dir),
           "--center-at", *[f"{c:.6f}" for c in center]]
    if sandboxed:
        cmd = sandbox.wrap(cmd, writable=[cand_dir], readonly=[layout.info(target_dir)])
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"the program took longer than {BUILD_TIMEOUT}s to build; simplify it"
    if p.returncode != 0:
        err = "\n".join(l for l in p.stderr.splitlines() if not l.startswith("FAILED, see"))
        return err.strip()[-1500:] or f"build failed (exit {p.returncode})"
    return None


def score(target_dir: Path, cand_dir: Path, weights=None, views=None, signal="both"):
    """Render-compare a built candidate. The checker (geo score, w_iou, table) sees only
    `views` (None = all) and `signal`; report["mean_iou"] stays the all-view mean."""
    rep = restrict(compare(target_dir, cand_dir, cand_dir / layout.DIFF), views)
    try:
        e3d = evaluate(target_dir, cand_dir)
    except Exception as e:  # never let offline scoring kill a run
        e3d = {"iou3d": None, "chamfer_x1000": None, "error": f"{type(e).__name__}: {e}"}
    info = json.loads(layout.info(cand_dir).read_text())
    size = (np.array(info["bbox_max"]) - np.array(info["bbox_min"])).tolist()
    w_iou, w_depth = weighted_means(rep, weights)
    return {"dir": cand_dir, "report": rep, "e3d": e3d, "size": size, "info": info,
            "geo_score": geo_score(rep, weights, signal=signal), "w_iou": w_iou, "w_depth": w_depth,
            "src": (cand_dir / "program.py").read_text()}


def gsolver_table(target_dir: Path, cand_dir: Path) -> str:
    """GT-vs-candidate property table (CADCodeVerify's geometric solver*; uses the GT)."""
    gt = target_dir / "gt.stl"
    gt = gt if gt.exists() else target_dir / "solid.stl"
    t = properties(trimesh.load(gt, force="mesh"))
    c = properties(trimesh.load(cand_dir / "solid.stl", force="mesh"))
    rows = [f"{'property':14s} {'target':>10s} {'current':>10s}"]
    rows += [f"{k:14s} {t[k]:10.1f} {c[k]:10.1f}" for k in t]
    return "\n".join(rows)


# ------------------------------------------------------------------ agent
class Agent:
    def __init__(self, model, think, repairs, backend=vlm.DEFAULT_BACKEND, sandboxed=False):
        self.model, self.think, self.repairs, self.backend = model, think, repairs, backend
        self.sandboxed = sandboxed
        self.llm_seconds = 0.0
        self.calls = 0
        self.prompt_tokens = 0
        self.output_tokens = 0

    def ask(self, messages):
        text, st = vlm.chat(messages, self.model, self.think, temperature=TEMPERATURE,
                            backend=self.backend)
        self.llm_seconds += st["seconds"]
        self.calls += 1
        self.prompt_tokens += st.get("prompt_tokens") or 0
        self.output_tokens += st.get("output_tokens") or 0
        return text, st

    def usage(self):
        return {"llm_seconds": round(self.llm_seconds, 1), "calls": self.calls,
                "prompt_tokens": self.prompt_tokens, "output_tokens": self.output_tokens}

    def write_program(self, user_msg, images, cand_dir, target_dir, center, allow_no_change=False,
                      tried=None):
        """Ask for a program; on build errors feed the error (with the CAD kernel's
        diagnosis) back up to `repairs` times. Repeat guard (edit feedback): a program equal,
        once normalised, to one in `tried` [(round, normalised lines)] is not built; the agent
        is told and the reply uses a repair slot.
        -> (status, attempts, transcript, change) with status "ok" | "failed" | "no_change" |
        "repeat_blocked" (the last reply was a blocked repeat)."""
        messages = [{"role": "system", "content": vlm.SYSTEM},
                    {"role": "user", "content": user_msg, "images": images}]
        transcript, change = [], (None, None)
        repeat = None
        for attempt in range(1, self.repairs + 2):
            text, st = self.ask(messages)
            transcript.append({"attempt": attempt, "reply": text, **st})
            if attempt == 1:
                change = vlm.parse_change(text)
                if allow_no_change and change[0] == "no_change":
                    return "no_change", attempt, transcript, change
            src = vlm.extract_code(text)
            repeat = None
            if src is not None and tried:
                norm = normalize_program(src)
                repeat = next((rnd for rnd, prog in tried if prog == norm), None)
            if repeat is not None:
                cand_dir.mkdir(parents=True, exist_ok=True)
                (cand_dir / "program.py").write_text(src)       # kept for the record, not built
                transcript[-1]["repeat_of"] = repeat
                err, follow = f"repeat of round {repeat}", vlm.repeat_prompt(repeat)
            else:
                err = "the reply had no ```python code block" if src is None else \
                    build(src, cand_dir, target_dir, center, self.sandboxed)
                follow = None if err is None else vlm.repair_prompt(err)
            transcript[-1]["error"] = err
            if err is None:
                return "ok", attempt, transcript, change
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": follow}]
        return ("repeat_blocked" if repeat is not None else "failed"), attempt, transcript, change

    def judge(self, target_img, cur_img, new_img, rng):
        """VLM visual review. Randomises which side is A to avoid position bias.
        -> (keep_new, details)"""
        new_is_b = rng.random() < 0.5
        a, b = (cur_img, new_img) if new_is_b else (new_img, cur_img)
        prompt = vlm.VLM_JUDGE.format(views=vlm.VIEWS_TEXT)
        text, _ = self.ask([{"role": "user", "content": prompt, "images": [target_img, a, b]}])
        pick = vlm.parse_judgement(text)
        keep_new = pick == ("B" if new_is_b else "A")
        return keep_new, {"reply": text, "pick": pick, "new_was": "B" if new_is_b else "A",
                          "keep": keep_new}

    # --- verification questions (CADCodeVerify)
    def questions(self, target_img):
        text, _ = self.ask([{"role": "user", "images": [target_img],
                             "content": vlm.QUESTIONS_PROMPT.format(views=vlm.VIEWS_TEXT)}])
        return vlm.parse_questions(text), text

    def answer(self, questions, img):
        qtxt = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
        text, _ = self.ask([{"role": "user", "images": [img],
                             "content": vlm.ANSWER_PROMPT.format(views=vlm.VIEWS_TEXT,
                                                                 questions=qtxt)}])
        return vlm.parse_answers(text, len(questions)), text

    def feedback(self, questions, answers):
        text, _ = self.ask([{"role": "user", "content": vlm.FEEDBACK_PROMPT.format(
            qa=vlm.qa_text(questions, answers))}])
        return text.strip()


def part_questions(agent, part_out: Path, target_img):
    """Verification questions for a part, written once from the TARGET and shared by all
    question arms. Sanity filter (ours): the questions are also answered on the target
    itself and only those answered "Yes" there are kept."""
    f = part_out / "questions.json"
    if f.exists():
        return json.loads(f.read_text())["questions"]
    qs, raw = agent.questions(target_img)
    ans, raw_a = agent.answer(qs, target_img) if qs else ([], "")
    kept = [q for q, a in zip(qs, ans) if a == "yes"]
    f.write_text(json.dumps({"questions": kept, "generated": qs, "target_answers": ans,
                             "reply": raw, "target_reply": raw_a}, indent=2))
    return kept


# ------------------------------------------------------------------ runs
def initial(agent, target_dir, out, lo, hi, center, target_img):
    """First program for a part written by the agent (no --init), shared by all arms."""
    d = out / "init"
    meta = d / layout.INTERNAL / "init.json"
    if layout.info(d).exists() and meta.exists():
        return json.loads(meta.read_text())["ok"]
    status, attempts, tr, _ = agent.write_program(vlm.initial_prompt(lo, hi), [target_img], d,
                                                  target_dir, center)
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps({"ok": status == "ok", "attempts": attempts,
                                "source": "agent", "transcript": tr}, indent=2))
    return status == "ok"


def stops_on_all_yes(spec, w_iou):
    """CADCodeVerify stops when every verification question is answered Yes. Arms that also
    see the geometric evidence only stop when that evidence agrees (high weighted IoU):
    a small VLM easily answers vague questions Yes while a view is clearly wrong."""
    return not spec["residuals"] or (w_iou is not None and w_iou >= ALL_YES_IOU)


def verdict_of(before, after):
    if before is None or after is None:
        return None
    return "beneficial" if after > before + BENEFIT else "harmful" if after < before - BENEFIT \
        else "neutral"


def diff_lines(old: str, new: str, cap=FB_DIFF_LINES):
    """Line diff for the agent's attempt log, blind to whitespace-only changes (the agent
    often reformats). -> ["- old line", "+ new line", ...]"""
    a = [l.rstrip() for l in old.splitlines() if l.strip()]
    b = [l.rstrip() for l in new.splitlines() if l.strip()]
    key = lambda ls: [re.sub(r"\s+", "", l) for l in ls]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=key(a), b=key(b),
                                                       autojunk=False).get_opcodes():
        if tag != "equal":
            out += [f"- {l.strip()}" for l in a[i1:i2]] + [f"+ {l.strip()}" for l in b[j1:j2]]
    if len(out) > cap:
        out = out[:cap] + [f"... ({len(out) - cap} more lines)"]
    return out


def _judge_reason(judge_d):
    """The judge's reasoning without its KEEP line (last paragraph, capped)."""
    if not judge_d or not judge_d.get("reply"):
        return None
    text = re.sub(r"KEEP\s+[AB]\b.*", "", judge_d["reply"], flags=re.I | re.S).strip()
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return (paras[-1] if paras else text)[:400] or None


class Branch:
    """`--patience K` (docs/ABLATION_PLAN.md F): depth-limited backtracking on one path.
    `anchor` is the last committed state, `head` the state the agent edits. Every built edit
    is judged against the anchor, never its parent, so a run of bad steps cannot drift:
      commit      the check passes vs the anchor       anchor = head = new, steps = 0
      tentative   it fails and steps < K               head = new, steps += 1
      rolled_back it fails on a branch with steps = K,  head = anchor, steps = 0
                  or the agent reverted to the anchor   (new is discarded)
      rejected    it fails at the anchor with K = 0 (or a no-op revert at the anchor)
    With K = 0 this is the plain keep/reject loop. The run's final state is the anchor."""

    def __init__(self, patience, start, start_round=0):
        self.k = patience
        self.anchor = self.head = start
        self.anchor_round = start_round
        self.steps = 0
        self.branch = []                    # rounds of the tentative edits on the head

    @property
    def on_branch(self):
        return self.head is not self.anchor

    def step(self, r, new, passed, reverted=False):
        if passed:
            self.anchor = self.head = new
            self.anchor_round, self.steps, self.branch = r, 0, []
            return "committed"
        if self.k and self.steps < self.k and not reverted:
            self.head = new
            self.steps += 1
            self.branch.append(r)
            return "tentative"
        if self.on_branch:
            self.rolled = self.branch + [r]     # the attempts that never beat the anchor
            self.head, self.steps = self.anchor, 0
            self.branch = []
            return "rolled_back"
        return "rejected"


def refine_part(agent, arm, target_dir, part_out, opts, lo, hi, center, target_img, weights,
                questions, seed, views=None):
    """views: the cameras the checker and the agent use (None = all; `--views worst` passes
    the one view picked from the round-0 program)."""
    spec = ARMS[arm]
    sig = opts.geo_signal
    gate = opts.gate == "on"
    # edit feedback (docs/FEEDBACK_PLAN.md): what each arm may be told about its own edits
    fb = opts.feedback
    fb_geo = spec["residuals"]                     # arms that see the geometric evidence
    fb_log = spec["accept"] != "always" or not gate  # gsolver keeps everything: history only
    attempts, history = [], []                     # attempts since the last kept edit
    rng = random.Random(seed)
    run_dir = part_out / arm
    run_dir.mkdir(parents=True, exist_ok=True)
    for old in run_dir.glob("round_*"):        # a rerun of this arm starts from scratch
        shutil.rmtree(old)
    (run_dir / "final").unlink(missing_ok=True)
    results = run_dir / "log.jsonl"
    results.unlink(missing_ok=True)
    t_start = time.time()
    u0 = agent.usage()

    def log(row):
        row = {"part": target_dir.name, "arm": arm, **row,
               "wall_seconds": round(time.time() - t_start, 1)}
        with results.open("a") as f:
            f.write(json.dumps(row, default=str) + "\n")
        print(f"  [{arm}] round {row['round']}: " + ", ".join(
            f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
            for k, v in row.items() if k in ("status", "accepted", "w_iou", "iou3d", "verdict",
                                             "stop")), flush=True)

    w = weights if opts.weights and views is None else None   # one view: nothing to cross-check
    cur = score(target_dir, part_out / "init", w, views, sig)
    log({"round": 0, "status": "ok", "accepted": True, "views": views or list(GRID_VIEWS),
         "mean_iou": cur["report"]["mean_iou"],
         "w_iou": cur["w_iou"], "depth_mae": cur["report"]["mean_depth_mae"],
         "geo_score": cur["geo_score"], **cur["e3d"]})
    best_geo, best_any = cur, cur          # GT-free and oracle choice of the best state
    br = Branch(opts.patience if gate else 0, cur)   # cur is always br.head
    stop = None
    r = 0
    for r in range(1, opts.rounds + 1):
        if opts.budget_seconds and time.time() - t_start > opts.budget_seconds:
            stop = "budget"
            break
        rd = run_dir / f"round_{r:02d}"
        rd.mkdir(parents=True, exist_ok=True)
        u_round = agent.usage()
        cur_img = render_grid(cur["dir"], views=views)
        cur_src_before = cur["src"]
        row = {"round": r}
        new = None
        qa = None

        # --- visual verification of the current state (question arms)
        if spec["qa"] and questions:
            ans, raw = agent.answer(questions, cur_img)
            qa = {"questions": questions, "answers": ans, "reply": raw}
            row["qa_yes"] = sum(a == "yes" for a in ans)
            row["qa_n"] = len(ans)
            if all(a == "yes" for a in ans) and stops_on_all_yes(spec, cur["w_iou"]):
                stop = "all_questions_yes"
                (rd / "conversation.json").write_text(json.dumps({"qa": qa}, indent=2))
                log({**row, "dir": _label_round(rd, "stopped").name, "status": "stopped", "accepted": False, "stop": stop,
                     **_usage_delta(u_round, agent.usage())})
                break
            if all(a == "yes" for a in ans):     # geometric evidence still says there is work
                qa["feedback"] = None
                row["qa_all_yes_continued"] = True
            else:
                qa["feedback"] = agent.feedback(questions, ans)

        # --- evidence for the edit
        images = [target_img, cur_img]
        table, detail, kinds = None, False, []
        if spec["residuals"] and opts.residuals:
            gviews = views or GRID_VIEWS
            if opts.residual_images:              # only the grids of the active signal
                if sig in ("both", "mask"):
                    labels = [f"{v}  IoU {cur['report']['views'][v]['iou']:.3f}" for v in gviews]
                    images.append(diff_grid(cur["dir"], "_overlay", labels, views))
                    kinds.append("overlay")
                if sig in ("both", "depth"):
                    images.append(diff_grid(cur["dir"], "_depth_err", views=views))
                    kinds.append("depth")
            if opts.detail:
                strip, dview = detail_strip(target_dir, cur["dir"], w, views=views,
                                            kind="_depth_err" if sig == "depth" else "_overlay")
                if strip:
                    images.append(strip)
                    detail = True
                    row["detail_view"] = dview
            table = residual_table(cur["report"], w, sig)
        if not opts.images:                       # ablation: refine without images
            images = []
        fb_text, tried, branch = None, None, None
        if br.on_branch:                          # --patience: tell the agent it is on a branch
            # the branch's diff vs the anchor, unless the attempt log already shows it
            show = fb == "none" or not fb_log or len(br.branch) > 1
            branch = vlm.branch_text(br.branch, br.anchor_round, br.k - br.steps + 1,
                                     diff_lines(br.anchor["src"], cur["src"]) if show else None)
        if fb != "none":
            shown = attempts[-FB_ATTEMPTS:] if fb_log else []
            effect = None
            if (fb == "image" and opts.images and fb_geo and sig != "depth" and shown
                    and shown[-1].get("effect_dir")):
                ed = shown[-1]["effect_dir"]
                cnt = json.loads((layout.diff_dir(ed) / "effect.json").read_text())
                gv = views or GRID_VIEWS
                images.append(diff_grid(ed, "_effect", [
                    f"{v}  fixed {cnt[v]['fixed']} px, broke {cnt[v]['broke']} px" for v in gv],
                    views=views))
                effect = len(images)
            fb_text = vlm.feedback_block(shown, history[-FB_HISTORY:], sig, effect)
            tried = [(e["round"], e["norm"]) for e in attempts if e.get("norm")]
            row["feedback_attempts"] = len(shown)
        msg = vlm.refine_prompt(
            cur["src"], lo, hi, cur["size"], n_images=len(images), residual_table=table,
            detail=detail, kernel=vlm.kernel_report(cur["info"]) if opts.kernel else None,
            qa_feedback=None if qa is None or not qa.get("feedback") else
            vlm.qa_text(qa["questions"], qa["answers"], only_failed=True) + "\n" + qa["feedback"],
            gsolver=gsolver_table(target_dir, cur["dir"]) if spec["gsolver"] else None,
            residual_images=kinds, views=views,
            detail_kind="depth error" if sig == "depth" else "residual", feedback=fb_text,
            branch=branch)
        status, n_tries, tr, (tag, why) = agent.write_program(
            msg, images, rd, target_dir, center, allow_no_change=True, tried=tried)
        row.update(status=status, attempts=n_tries, repairs_used=n_tries - 1,
                   change_tag=tag, change=why)
        blocked = [t["repeat_of"] for t in tr if t.get("repeat_of") is not None]
        if fb != "none":
            row["repeat_blocked"] = len(blocked)
        entry = None
        decision = {}
        if status == "no_change":
            stop = "no_change"
            row.update(accepted=False, verdict=None, stop=stop)
        elif status == "ok":
            new = score(target_dir, rd, w, views, sig)
            base, base_round = br.anchor, br.anchor_round   # = cur unless on a branch
            geo_keep, geo_d = geo_accept(base["report"], new["report"], w, signal=sig)
            a, b = base["e3d"].get("iou3d"), new["e3d"].get("iou3d")
            judge_d = None
            mode = spec["accept"]
            gate = opts.gate == "on"
            need_judge = opts.shadow_judge or (gate and (
                mode == "judge" or (mode == "hybrid" and (geo_keep or geo_d["inconclusive"]))))
            if need_judge:
                _, judge_d = agent.judge(target_img, cur_img, render_grid(rd, views=views), rng)
            if mode == "judge":
                keep = judge_d["keep"]
            elif mode == "geo":
                keep = geo_keep
            elif mode == "hybrid":
                keep = judge_d["keep"] if geo_d["inconclusive"] else geo_keep and judge_d["keep"]
            elif mode == "oracle":
                keep = a is not None and b is not None and b > a
            else:  # always
                keep = True
            if not gate:                          # ablation: the checker informs, never blocks
                keep = True
            decision = {"rule": mode if gate else "gate_off", "geo": geo_d, "judge": judge_d}
            # why the edit ended the way it did, as far as this arm may know it
            if not gate:
                reason = "gate_off"
            elif keep:
                reason = "kept"
            elif mode == "judge" or (mode == "hybrid" and judge_d is not None
                                     and not judge_d["keep"]):
                reason = "judge"
            elif mode in ("geo", "hybrid"):
                reason = geo_d["reason"]
            else:
                reason = None                     # oracle: rejected, without the GT reason
            row["reject_reason"] = None if keep else reason
            reverted = br.on_branch and normalize_program(new["src"]) == \
                normalize_program(base["src"])
            outcome = br.step(r, new, keep, reverted)
            if br.k:
                row.update(patience_outcome=outcome, anchor_round=base_round,
                           branch_depth=br.steps, reverted=reverted)
            if fb != "none":
                entry = {"outcome": {"committed": "kept"}.get(outcome, outcome), "reason": reason,
                         "anchor_round": base_round if br.k else None,
                         "rolled": br.rolled if outcome == "rolled_back" else None,
                         "reverted": reverted,
                         "geo_keep": geo_keep, "judge": _judge_reason(judge_d)
                         if reason == "judge" else None,
                         **{k: geo_d[k] for k in ("gain", "worst_view", "worst_view_drop",
                                                  "min_gain", "max_view_drop")}}
                if fb_geo:
                    entry["delta"] = edit_delta(base["report"], new["report"], w, sig)
                if fb == "image" and fb_geo and sig != "depth" and not keep:
                    write_effect_images(target_dir, base["dir"], rd, rd / layout.DIFF, views)
            row.update(accepted=keep, verdict=verdict_of(a, b),
                       geo_decision=geo_keep, geo_gain=geo_d["gain"],
                       geo_inconclusive=geo_d["inconclusive"],
                       vlm_decision=None if judge_d is None else judge_d["keep"],
                       mean_iou=new["report"]["mean_iou"], w_iou=new["w_iou"],
                       depth_mae=new["report"]["mean_depth_mae"], geo_score=new["geo_score"],
                       kernel_warnings=len(new["info"].get("ops", {}).get("warnings", [])),
                       **new["e3d"], iou3d_before=a)
            if (new["e3d"].get("iou3d") or -1) > (best_any["e3d"].get("iou3d") or -1):
                best_any = new
            cur = br.head
            if outcome == "committed" and cur["geo_score"] > best_geo["geo_score"]:
                best_geo = cur
        else:
            row.update(accepted=False, verdict=None)
            if status in ("failed", "repeat_blocked"):
                row["reject_reason"] = status
                if fb != "none":
                    entry = {"outcome": status, "error": tr[-1].get("error"),
                             "repeat_of": blocked[-1] if blocked else None}
        row.update(_usage_delta(u_round, agent.usage()))
        (rd / "conversation.json").write_text(json.dumps(
            {"prompt": msg, "transcript": tr, "decision": decision, "qa": qa}, indent=2,
            default=str))
        label = {"ok": {"committed": "kept", "tentative": "tentative",
                        "rolled_back": "rolled-back"}.get(outcome, "rejected") if status == "ok"
                 else None, "failed": "failed",
                 "no_change": "no-change", "repeat_blocked": "repeat-blocked"}[status]
        rd = _label_round(rd, label)
        if new is not None:               # cur / best_* may point at this round's state
            new["dir"] = rd
        if fb != "none":                  # update the attempt log and the round history
            hist = f"round {r}: " + {"kept": "kept", "rejected": "rejected",
                                     "failed": "did not build",
                                     "repeat_blocked": "repeat, not built",
                                     "tentative": "kept tentatively (below the last committed "
                                                  f"program, round {(entry or {}).get('anchor_round')})",
                                     "rolled_back": "rolled back to round "
                                                    f"{(entry or {}).get('anchor_round')}"}.get(
                (entry or {}).get("outcome"), "NO_CHANGE")
            if entry is not None:
                src_f = rd / "program.py"
                new_src = src_f.read_text() if src_f.exists() else None
                entry.update(round=r, tag=tag, change=why,
                             diff=None if new_src is None else diff_lines(cur_src_before, new_src),
                             norm=None if new_src is None else normalize_program(new_src))
                if (rd / layout.DIFF / f"{(views or GRID_VIEWS)[0]}_effect.png").exists():
                    entry["effect_dir"] = rd
                if fb_geo and entry.get("gain") is not None:
                    hist += f", geometric score {entry['gain']:+.4f}"
                    d = entry.get("delta")
                    if entry["outcome"] == "kept" and d and sig != "depth":
                        hist += f" (best view {d['best_view']} IoU {d['best_change']:+.3f})"
                if why:
                    hist += f' — "{why[:120]}"'
                if entry["outcome"] == "kept":
                    attempts = [entry] if not gate else []   # gate off: show the last edit
                else:
                    attempts.append(entry)
            history.append(hist)
        row["dir"] = rd.name
        log(row)
        if stop:
            break
    else:
        stop = "rounds"
    cur = br.anchor                       # never an uncommitted branch
    os.symlink(os.path.relpath(cur["dir"], run_dir), run_dir / "final",
               target_is_directory=True)
    final = {"part": target_dir.name, "arm": arm, "stop": stop, "rounds_run": r,
             "final_dir": str(cur["dir"]), "mean_iou": cur["report"]["mean_iou"],
             "w_iou": cur["w_iou"], **cur["e3d"], "patience": br.k,
             "ended_on_branch": br.on_branch,
             "best_geo": {"dir": str(best_geo["dir"]), **best_geo["e3d"]},
             "best_oracle": {"dir": str(best_any["dir"]), **best_any["e3d"]},
             "wall_seconds": round(time.time() - t_start, 1),
             **_usage_delta(u0, agent.usage())}
    (run_dir / "result.json").write_text(json.dumps(final, indent=2, default=str))
    return final


def _label_round(rd: Path, label: str) -> Path:
    """round_02 -> round_02_kept / _rejected / _failed / _no-change / _stopped."""
    dest = rd.with_name(f"{rd.name}_{label}")
    rd.rename(dest)
    return dest


def _usage_delta(a, b):
    return {"llm_seconds": round(b["llm_seconds"] - a["llm_seconds"], 1),
            "calls": b["calls"] - a["calls"],
            "prompt_tokens": b["prompt_tokens"] - a["prompt_tokens"],
            "output_tokens": b["output_tokens"] - a["output_tokens"]}


def prepare_init(args, agent, target, part_out, lo, hi, center, target_img):
    """Build the shared first program (cadrille's, or the agent's own). -> ok"""
    if args.init is None:
        return initial(agent, target, part_out, lo, hi, center, target_img)
    d = part_out / "init"
    meta = d / layout.INTERNAL / "init.json"
    if meta.exists() and layout.info(d).exists():
        return json.loads(meta.read_text())["ok"]
    f = args.init / f"{target.name}.py"
    if not f.exists():
        err = f"no starting program {f}"
    else:
        err = build(f.read_text(), d, target, center, args.sandbox)
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps({"ok": err is None, "error": err, "source": str(f)}))
    return err is None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", type=Path, nargs="+", help="target dirs (renders + depth.npz)")
    ap.add_argument("--arm", default="main",
                    help=f"comma list of {sorted(ARMS)}, or 'main' ({','.join(MAIN_ARMS)}) or 'all'")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--budget-seconds", type=float, default=None,
                    help="wall-clock budget per part and arm (GATOR-style); stops early")
    ap.add_argument("--repairs", type=int, default=2, help="retries after a build error")
    ap.add_argument("--backend", default=vlm.DEFAULT_BACKEND, choices=sorted(vlm.BACKENDS),
                    help="vertex = Gemini on Vertex AI (.env), ollama = local model, echo = dry run")
    ap.add_argument("--model", default=None,
                    help=f"default: VERTEX_MODEL from .env (vertex) or {vlm.OLLAMA_MODEL} (ollama)")
    ap.add_argument("--think", action="store_true", help="let the model think (slower)")
    ap.add_argument("--init", type=Path, default=None,
                    help="dir of <part>.py starting programs (e.g. cadrille_init.py output); "
                         "default: the agent writes the first program")
    ap.add_argument("--shadow-judge", action="store_true",
                    help="also run the VLM judge in arms that don't use it (costs calls)")
    # ablations (each one switches a component off)
    ap.add_argument("--no-weights", dest="weights", action="store_false",
                    help="plain mean over views instead of view-confidence weights")
    ap.add_argument("--no-kernel", dest="kernel", action="store_false",
                    help="don't show the CAD-kernel report")
    ap.add_argument("--no-residuals", dest="residuals", action="store_false",
                    help="geo/hybrid: gate on the check but show the agent no residuals")
    ap.add_argument("--no-residual-images", dest="residual_images", action="store_false",
                    help="geo/hybrid: residual table only, no residual images")
    ap.add_argument("--no-detail", dest="detail", action="store_false",
                    help="no zoom on the largest residual")
    ap.add_argument("--no-images", dest="images", action="store_false",
                    help="refine from text only (CADCodeVerify ablation)")
    ap.add_argument("--geo-signal", default="both", choices=SIGNALS,
                    help="what the geometric check uses, for both the agent's evidence and the "
                         "keep decision: silhouette + depth (both), silhouette only (mask) or "
                         "depth error only (depth; no per-view IoU guard)")
    ap.add_argument("--views", default="all", choices=["all", "worst"],
                    help="worst: use only the view where the round-0 program is most wrong, for "
                         "the agent's images and table and for the check (weights off)")
    ap.add_argument("--feedback", default="image", choices=["none", "text", "image"],
                    help="edit feedback (docs/FEEDBACK_PLAN.md): text = attempt log of edits "
                         "not kept since the last kept one, round history and repeat guard; "
                         "image = text + an edit-effect image of the latest attempt")
    ap.add_argument("--gate", default="on", choices=["on", "off"],
                    help="off: keep every built edit; the check still runs and is logged "
                         "(geo_decision), and best_geo still picks a state at the end")
    ap.add_argument("--patience", type=int, default=0,
                    help="geo/oracle arms, gate on: an edit that fails the check stays as a "
                         "tentative branch for up to K more rounds; the branch is committed only "
                         "if it beats the last committed state, else rolled back (ABLATION_PLAN F)")
    ap.add_argument("--sandbox", action="store_true",
                    help="build model-written programs inside a bubblewrap sandbox "
                         "(Linux only: no network, no home dir, only the output dir writable)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--name", default=None,
                    help="run label; the run goes to runs/<date>_<name> (default name: "
                         "<arms>_<model>)")
    ap.add_argument("--out", type=Path, default=None,
                    help="exact run folder instead of runs/<date>_<name>")
    args = ap.parse_args(argv)

    arms = list(MAIN_ARMS) if args.arm == "main" else list(ARMS) if args.arm == "all" \
        else [a.strip() for a in args.arm.split(",")]
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        ap.error(f"unknown arm(s) {unknown}")
    if args.views == "worst" and any(ARMS[a]["qa"] or ARMS[a]["accept"] in ("judge", "hybrid")
                                     for a in arms):
        ap.error("--views worst is for the geo and oracle arms (the questions and the judge "
                 "assume the 4-view grid)")
    if args.patience < 0:
        ap.error("--patience must be >= 0")
    if args.patience and (args.gate == "off" or any(ARMS[a]["accept"] not in ("geo", "oracle")
                                                    for a in arms)):
        ap.error("--patience needs --gate on and the geo or oracle arm (it compares every edit "
                 "with the last committed state)")
    if args.sandbox:
        try:
            sandbox.check()
        except sandbox.SandboxUnavailable as e:
            ap.error(str(e))
    if args.model is None:
        try:
            args.model = vlm.default_model(args.backend)
        except RuntimeError as e:
            ap.error(str(e))
    rig = load_rig()
    targets = [t for t in args.targets if layout.is_rendered(t)]
    if args.out is None:
        name = args.name or f"{'-'.join(arms) if len(arms) < 4 else args.arm}_{args.model}"
        args.out = RUNS / f"{datetime.date.today():%Y-%m-%d}_{re.sub(r'[^A-Za-z0-9._-]+', '-', name)}"
    args.out = args.out.resolve()          # builds run with cwd=ROOT
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "config.json").write_text(json.dumps(
        {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()
         if k != "targets"} | {"arms": arms, "n_targets": len(targets),
                               "started": f"{datetime.datetime.now():%Y-%m-%d %H:%M}",
                               "prices": vertex_ai.prices() if args.backend == "vertex" else None,
                               "targets": {t.name: str(t) for t in targets}}, indent=2))
    print(f"run folder: {args.out}  (open README.md there)", flush=True)
    with report.Tee(args.out / "log.txt"):
        for target in targets:
            part_out = args.out / "parts" / target.name
            (part_out / layout.INTERNAL).mkdir(parents=True, exist_ok=True)
            lo, hi = measure_bbox(target, rig)
            center = (lo + hi) / 2
            target_img = render_grid(target)
            weights = view_weights(target, rig)
            (part_out / layout.INTERNAL / "view_weights.json").write_text(
                json.dumps(weights, indent=2))
            agent = Agent(args.model, args.think, args.repairs, args.backend, args.sandbox)
            print(f"{target.name}: measured bbox {np.round(hi - lo, 1).tolist()} units",
                  flush=True)
            try:
                if not prepare_init(args, agent, target, part_out, lo, hi, center, target_img):
                    print("  no valid first program; skipping part", flush=True)
                    continue
                questions = part_questions(agent, part_out, target_img) \
                    if any(ARMS[a]["qa"] for a in arms) else []
                views, arm_img = None, target_img
                if args.views == "worst":            # fixed for the run, from round 0
                    init_dir = part_out / "init"
                    compare(target, init_dir, init_dir / layout.DIFF)
                    views = [progress.worst_view(init_dir)]
                    arm_img = render_grid(target, views=views)
                    lo, hi = measure_bbox(target, rig, views)   # strict: this view's depth only
                    (part_out / layout.INTERNAL / "views.json").write_text(json.dumps(
                        {"views": views, "rule": "worst view of the round-0 program",
                         "bbox_size_one_view": np.round(hi - lo, 1).tolist()}))
                    print(f"  one view: {views[0]}", flush=True)
                for i, arm in enumerate(arms):
                    refine_part(agent, arm, target, part_out, args, lo, hi, center, arm_img,
                                weights, questions, args.seed + i, views)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                print(f"  {target.name} crashed; continuing with the next part", flush=True)
            report.write(args.out)              # README / results stay current mid-run
        report.write(args.out, finished=True)
    print(f"done: {args.out / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
