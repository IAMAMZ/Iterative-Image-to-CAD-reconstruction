"""Talk to the agent's vision-language model, and the prompts the agent uses.

Backends (pick with `backend=`):
  vertex  Gemini on Vertex AI (vertex_ai.py); project + model come from .env (default)
  ollama  a local open-weight VLM through `ollama serve` (e.g. gemma4:12b); no API keys
  echo    a fake agent for tests and dry runs: it perturbs one number of the current
          program, answers judge/question prompts deterministically, never calls a model
Every backend returns (reply text, stats) with token counts, so runs can be costed.
"""
import base64
import hashlib
import json
import random
import re
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"


# ------------------------------------------------------------------ backends
def _ollama(messages, model, think, temperature, num_ctx, max_tokens, deadline):
    msgs = [{**m, "images": [base64.b64encode(b).decode() for b in m["images"]]}
            if m.get("images") else m for m in messages]
    body = {"model": model, "messages": msgs, "stream": False, "think": think,
            "options": {"temperature": temperature, "num_ctx": num_ctx,
                        "num_predict": max_tokens}}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=deadline) as r:
        out = json.loads(r.read())
    stats = {"seconds": round(time.time() - t0, 1),
             "prompt_tokens": out.get("prompt_eval_count"),
             "output_tokens": out.get("eval_count"),
             "cut_off": "max_tokens" if out.get("done_reason") == "length" else None}
    return out.get("message", {}).get("content", ""), stats


_NUM = re.compile(r"(?<![\w.])(\d+\.?\d*)(?![\w.])")


def _echo(messages, model, think, temperature, num_ctx, max_tokens, deadline):
    """Deterministic fake agent (seeded by the conversation) for tests and dry runs."""
    last = messages[-1]["content"]
    h = hashlib.sha1("".join(m["content"] for m in messages).encode())
    for m in messages:                        # images too, so new renders give new answers
        for im in m.get("images") or []:
            h.update(im)
    seed = int(h.hexdigest()[:8], 16)
    rng = random.Random(seed)
    if "KEEP A" in last and "KEEP B" in last:
        text = f"Both are close.\nKEEP {rng.choice('AB')}"
    elif QUESTIONS_MARK in last:
        text = "\n".join(f"{i}. {q}" for i, q in enumerate(
            ["Is the part a single connected solid?", "Does the part have a through-hole?",
             "Is the part longer along X than along Y?"], 1))
    elif ANSWER_MARK in last:
        qs = parse_questions(last.split("Questions:", 1)[-1])
        text = "\n".join(f"{i}. **{q}**\n- **Answer:** {rng.choice(['Yes', 'Yes', 'No', 'Unclear'])}"
                         f"\n- **Reasoning:** echo." for i, q in enumerate(qs, 1))
    elif FEEDBACK_MARK in last:
        text = "Make the main body slightly longer."
    else:
        code = None
        for m in reversed(messages):
            code = extract_code(m["content"])
            if code:
                break
        if code is None:
            text = ("CHANGE: structural - start from a block.\n```python\nimport cadquery as cq\n"
                    "result = cq.Workplane('XY').box(100, 60, 20)\n```")
        elif rng.random() < 0.1:
            text = "NO_CHANGE"
        else:
            nums = list(_NUM.finditer(code))
            if nums:
                m = rng.choice(nums)
                v = float(m.group(1)) * rng.choice([0.9, 1.1])
                code = code[:m.start()] + f"{v:.3g}" + code[m.end():]
            text = f"CHANGE: dimensional - adjust one dimension.\n```python\n{code}```"
    n_in = sum(len(m["content"]) for m in messages) // 4
    return text, {"seconds": 0.0, "prompt_tokens": n_in, "output_tokens": len(text) // 4,
                  "cut_off": None}


def _vertex(messages, model, think, temperature, num_ctx, max_tokens, deadline):
    import vertex_ai  # lazy: only this backend needs google-genai and a GCP project
    return vertex_ai.chat(messages, model, think, temperature, num_ctx, max_tokens, deadline)


BACKENDS = {"vertex": _vertex, "ollama": _ollama, "echo": _echo}
DEFAULT_BACKEND = "vertex"
OLLAMA_MODEL = "gemma4:12b"


def default_model(backend: str) -> str:
    """Model used when none is given: VERTEX_MODEL from .env for vertex, gemma4 otherwise."""
    if backend == "vertex":
        import vertex_ai
        return vertex_ai.default_model()
    return OLLAMA_MODEL if backend == "ollama" else "echo"


def chat(messages, model=None, think=False, temperature=1.0, num_ctx=16384,
         max_tokens=2500, deadline=480, backend=DEFAULT_BACKEND):
    """messages: [{"role", "content", "images": [png bytes, ...]}] -> (reply text, stats)."""
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend!r}; choose from {sorted(BACKENDS)}")
    model = model or default_model(backend)
    return BACKENDS[backend](messages, model, think, temperature, num_ctx, max_tokens, deadline)


# ------------------------------------------------------------------ code handling
_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)
_ALLOWED_IMPORTS = {"cadquery", "math"}
_FORBIDDEN = re.compile(r"\b(open|exec|eval|compile|__import__|globals|locals|getattr|setattr|"
                        r"input|breakpoint)\s*\(|\b(os|sys|subprocess|shutil|socket|pathlib)\.")


def extract_code(text: str) -> str | None:
    """Last ```python block in the reply (models sometimes show a draft first)."""
    blocks = _FENCE.findall(text)
    return blocks[-1].strip() + "\n" if blocks else None


def check_code(src: str) -> str | None:
    """Cheap safety net before running model-written code. Returns an error or None."""
    for line in src.splitlines():
        m = re.match(r"\s*(?:from\s+(\S+)\s+import|import\s+(\S+))", line)
        if m:
            mod = (m.group(1) or m.group(2)).split(".")[0].rstrip(",")
            if mod not in _ALLOWED_IMPORTS:
                return f"import of '{mod}' is not allowed; only `import cadquery as cq` and `import math`"
    if _FORBIDDEN.search(src):
        return "the program may only build geometry (no files, os, exec, eval, ...)"
    if not re.search(r"^result\s*=", src, re.M):
        return "the program must assign the final solid to a variable named `result`"
    return None


def parse_change(text: str):
    """-> ("no_change", None) | (tag, sentence) | (None, None). Tag is structural,
    dimensional or positional (CADCodeVerify's feedback types)."""
    if re.match(r"^\s*NO_CHANGE\b", text) and extract_code(text) is None:
        return "no_change", None
    m = re.search(r"CHANGE:\s*\**\s*(structural|dimensional|positional)\**\s*[-:—–]*\s*(.*)",
                  text, re.I)
    if m:
        return m.group(1).lower(), m.group(2).strip()[:300]
    return None, None


# ------------------------------------------------------------------ prompts
SYSTEM = """You are a CAD engineer. You write and edit CadQuery (Python) programs that \
rebuild a mechanical part from pictures of it.

Rules for every program you write:
- Lengths are in the part's own units (the part's longest side is about 200 units). Z is up.
- Start with `import cadquery as cq` (you may also `import math`; nothing else).
- Assign the final single solid to a variable named `result`.
- Reply with exactly one ```python code block containing the whole program. It must run on \
its own: keep every line it needs, including the lines that create workplanes \
(e.g. `w0 = cq.Workplane(...)`) and the `import`.

When you edit an existing program:
- Treat the current program as the scaffold: keep its coordinate frame, orientation and \
scale, and keep every feature the pictures confirm. Make a targeted, local change.
- Do not add features the pictures do not show, and do not remove features they do show.
- Start your reply with one line `CHANGE: <structural|dimensional|positional> - <what you \
change, one sentence>`, then the code block. If nothing worthwhile is left to fix, reply \
with exactly `NO_CHANGE` and no code.

Coordinate frames of the workplanes:
- cq.Workplane("XY"): local x = +X, local y = +Y, extrudes towards +Z.
- cq.Workplane("XZ"): local x = +X, local y = +Z, extrudes towards -Y (use both=True to centre on Y=0).
- cq.Workplane("YZ"): local x = +Y, local y = +Z, extrudes towards +X.
- cq.Workplane("XY", origin=(x, y, z)) moves the workplane's origin.
"""

VIEW_DESC = {   # rig.py cameras, in grid order
    "top_front": "from the front (-Y side), above; image right = +X",
    "top_right": "from the right (+X side), above; image right = +Y",
    "top_back": "from the back (+Y side), above; image right = -X",
    "top_left": "from the left (-X side), above; image right = -Y",
}
GRID_POS = ("top-left", "top-right", "bottom-left", "bottom-right")


PHOTO_NOTE = ("Reconstructions are rendered from exactly these cameras as grey shaded solids. "
              "Ignore the table, background, colour and texture of the photos: only the shape "
              "is compared.")


def photo_views_text(desc: dict, views=None):
    """views_text for a target with its own photo cameras (RealCAD; data/realcad_targets.py
    stores `desc` = {view: where the camera is, in the part's axes} in info.json "view_desc")."""
    views = list(desc) if views is None else list(views)
    if len(views) == 1:
        v = views[0]
        return (f'The picture is a PHOTO of the real part lying on a table, cropped around the '
                f'part, taken by one calibrated camera "{v}". In the part\'s own axes (the X, Y, '
                f"Z your CadQuery program uses) the camera is {desc[v]}. "
                + PHOTO_NOTE.replace("these cameras", "this camera"))
    lines = [f"The picture is a 2x2 grid of {len(views)} PHOTOS of the real part lying on a "
             "table, each cropped around the part. The part was turned on the table between "
             "photos. In the part's own axes (the X, Y, Z your CadQuery program uses) the "
             "cameras are:"]
    lines += [f'- {p} "{v}": {desc[v]}' for p, v in zip(GRID_POS, views)]
    return "\n".join(lines + [PHOTO_NOTE])


def views_text(views=None, desc=None):
    """How the pictures are laid out: the 2x2 grid of all 4 cameras, or a single camera
    (ablation `--views worst`). desc: the target's own camera descriptions (photo targets)."""
    if desc:
        return photo_views_text(desc, views)
    views = list(VIEW_DESC) if views is None else list(views)
    if len(views) == 1:
        v = views[0]
        return (f'The picture shows the part seen by one calibrated camera, "{v}": '
                f"{VIEW_DESC[v]}. The camera is 45 degrees above the table, like a photo of a "
                "part on a table. +Z points up in the image; the underside is never seen.")
    return ("The picture is a 2x2 grid of the same part seen by 4 calibrated cameras, like "
            "photos of a part on a table: each camera is 45 degrees above the table, and they "
            "are 90 degrees apart around the part. +Z points up in every image; the underside "
            "is never seen.\n" + "\n".join(f'- {p} "{v}": {VIEW_DESC[v]}'
                                           for p, v in zip(GRID_POS, views)))


VIEWS_TEXT = views_text()


def bbox_text(lo, hi, one_view=False):
    size = [h - l for l, h in zip(lo, hi)]
    if one_view:      # one depth map sees only the near surfaces: a lower bound
        return (f"Measured from this camera's depth map, the visible surfaces of the part span "
                f"about {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} units (X x Y x Z). Parts "
                "the camera cannot see may extend further, so the real size is at least this. "
                "Its exact position does not matter; only shape and size are compared.")
    return (f"Measured from the calibrated depth maps, the part's bounding box is about "
            f"{size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} units (X x Y x Z). "
            f"Its exact position does not matter; only shape and size are compared.")


def initial_prompt(lo, hi, view_desc=None):
    return (f"Here is the target part.\n{views_text(desc=view_desc)}\n\n{bbox_text(lo, hi)}\n\n"
            "Look at the main body first (plate, block, L-shape, cylinder, steps), then "
            "holes, slots, cut-outs and fillets. Write a CadQuery program that rebuilds it. "
            "Start your reply with `CHANGE: structural - first version`.")


def kernel_report(info: dict) -> str:
    """CAD-kernel report of the current program from generate_solid.py's info.json."""
    warns = info.get("ops", {}).get("warnings", [])
    lines = [f"The program builds a valid solid: {info.get('n_solids', '?')} solid piece(s), "
             f"{info.get('n_faces', '?')} faces, volume {info.get('volume', float('nan')):.0f} "
             "cubic units."]
    if warns:
        lines.append("The CAD kernel flagged these operations (each one is legal but probably "
                     "not what was meant; e.g. no_effect = the operation changed nothing, "
                     "split_into_pieces = the part fell apart):")
        lines += [f"  {w}" for w in warns[:8]]
    else:
        lines.append("The CAD kernel flagged no operations.")
    return "\n".join(lines)


RESIDUAL_TEXT = {
    "overlay": "the silhouette residual for the same {views}: GREY = correct, RED = material "
               "the target has but we are MISSING, BLUE = EXTRA material we have but the "
               "target does not.",
    "depth": "the depth error where both cover the pixel: pale = correct, dark red/purple = "
             "surface at the wrong depth (wrong thickness or height).",
}


def refine_prompt(program, lo, hi, cand_size=None, *, n_images=2, residual_table=None,
                  detail=False, kernel=None, qa_feedback=None, gsolver=None,
                  residual_images=("overlay", "depth"), views=None, detail_kind="residual",
                  feedback=None, branch=None, view_desc=None):
    """The edit request. Which evidence goes in is decided by the arm (see refine.ARMS) and
    the ablation flags: `residual_images` lists the residual grids sent (images 3, 4, ...),
    `views` the cameras shown (None = all 4). view_desc: the target's own camera
    descriptions (photo targets; None = the fixed rig's)."""
    nv = len(view_desc or VIEW_DESC) if views is None else len(views)
    cams = "camera" if nv == 1 else f"{nv} cameras"
    lines = []
    if n_images:
        lines += ["Image 1 is the TARGET part. Image 2 is our CURRENT reconstruction, rendered "
                  f"by the same {cams}.", views_text(views, view_desc)]
    lines += ["", bbox_text(lo, hi, one_view=views is not None and len(views) == 1)]
    if cand_size is not None:
        lines.append("The current reconstruction's bounding box is "
                     f"{cand_size[0]:.1f} x {cand_size[1]:.1f} x {cand_size[2]:.1f} units.")
    if residual_table is not None:
        k = 3
        if n_images > 2 and residual_images:
            lines.append("")
            for kind in residual_images:
                lines.append(f"Image {k} is " + RESIDUAL_TEXT[kind].format(
                    views="view" if nv == 1 else f"{nv} views"))
                k += 1
        if detail:
            lines.append(f"Image {k} zooms into the largest residual: target | current | "
                         f"{detail_kind}.")
        what = "IoU 1.0 = perfect outline; " if "IoU" in residual_table.splitlines()[0] else ""
        trust = "" if nv == 1 else ("weight = how much that camera is trusted, views that "
                                    "disagree with the others count less")
        note = f" ({what}{trust})".replace("; )", ")") if what or trust else ""
        lines += [f"Per-view numbers from {'the camera' if nv == 1 else f'all {nv} cameras'}"
                  f"{note}:", residual_table]
    if kernel:
        lines += ["", "CAD kernel report for the current program:", kernel]
    if qa_feedback:
        lines += ["", "Visual verification of the current reconstruction found these problems:",
                  qa_feedback]
    if gsolver:
        lines += ["", "Geometric properties, target vs current:", gsolver]
    if branch:
        lines += ["", branch]
    if feedback:
        lines += ["", feedback]
    lines += ["", "Current program:", f"```python\n{program.strip()}\n```", "",
              "Find the single biggest geometric difference between the target and the current "
              "reconstruction, fix it, and reply in the format from the rules (CHANGE line, then "
              "the complete revised program in one ```python block), or NO_CHANGE."]
    return "\n".join(lines)


# --------------------------------------------- edit feedback (docs/FEEDBACK_PLAN.md)
FEEDBACK_RULE = ("Use these attempts: do not repeat a rejected change. If its feature was right "
                 "but the size or position was off, try a different size or the other "
                 "direction; otherwise fix a different difference.")
_MOSTLY = {"extra": "mostly EXTRA material (blue in the residual image)",
           "missing": "mostly MISSING material (red in the residual image)",
           "depth": "mostly surfaces at the wrong depth"}


def _reason_text(e):
    """One line: why the attempt ended the way it did (only what the arm may see)."""
    out, why = e["outcome"], e.get("reason")
    if out == "failed":
        err = (e.get("error") or "").strip().splitlines()[-3:]
        return "FAILED TO BUILD — " + " / ".join(l.strip() for l in err)[:300]
    if out == "repeat_blocked":
        return f"NOT BUILT — the same program as your attempt in round {e.get('repeat_of')}"
    if out == "rolled_back":
        rounds = ", ".join(str(x) for x in e.get("rolled") or [])
        how = "you reverted to it" if e.get("reverted") else \
            f"the branch (attempts in rounds {rounds}) never beat it"
        return (f"ROLLED BACK to the program committed in round {e.get('anchor_round')} — {how}; "
                "the current program below is that one again")
    head = {"rejected": "REJECTED", "kept": "KEPT",
            "tentative": "KEPT TENTATIVELY"}[out]
    g = e.get("gain")
    if out == "tentative":
        what = f"view {e['worst_view']} lost {-e['worst_view_drop']:.3f} IoU" \
            if why == "view_drop" else f"geometric score {g:+.4f}"
        return (f"{head} — compared with the last committed program (round "
                f"{e.get('anchor_round')}): {what}, so it was not committed but became a "
                "tentative branch")
    if why == "gain":
        return f"{head} — the geometric score fell by {-g:.4f} (an edit is kept only if it " \
               f"rises by more than {e['min_gain']:g})"
    if why == "view_drop":
        return (f"{head} — the overall score rose by {g:.4f}, but view {e['worst_view']} lost "
                f"{-e['worst_view_drop']:.3f} IoU (more than the {e['max_view_drop']:g} allowed): "
                "it fixed one view and broke another")
    if why == "inconclusive":
        return (f"{head} — it changed the geometric score by less than {e['min_gain']:g}: "
                "the edit had almost no visible effect (no real change of shape, or a change "
                "no camera sees)")
    if why == "judge":
        return f"{head} — the visual reviewer preferred the previous version: {e.get('judge')}"
    if why == "gate_off":
        verdict = "would have kept it" if e.get("geo_keep") else "would have rejected it"
        return f"{head} (every edit is kept in this run) — the geometric check {verdict}; " \
               f"score change {g:+.4f}"
    return head                                   # e.g. the oracle arm: no reason given


def _delta_table(delta, signal):
    mask, depth = signal in ("both", "mask"), signal in ("both", "depth")
    cols = (["IoU", "missing px", "extra px"] if mask else []) + (["depth MAE"] if depth else [])
    rows = [f"{'view':10s}" + "".join(f"{c:16s}" for c in cols)]
    for v, m in delta["views"].items():
        cells = []
        if mask:
            cells += [f"{m['iou'][0]:.3f} → {m['iou'][1]:.3f}",
                      f"{m['missing'][0]} → {m['missing'][1]}",
                      f"{m['extra'][0]} → {m['extra'][1]}"]
        if depth:
            a, b = m["depth"]
            cells.append("n/a" if a is None or b is None else f"{a:.2f} → {b:.2f}")
        rows.append(f"{v:10s}" + "".join(f"{c:16s}" for c in cells).rstrip())
    return rows


def feedback_block(attempts, history, signal="both", effect_image=None):
    """The edit-feedback text (FEEDBACK_PLAN 3.1): the attempts since the last kept edit
    (newest last, already capped by the caller) and a one-line history of every round.
    `effect_image` = the image number of the latest attempt's edit-effect grid, or None."""
    lines = []
    if attempts:
        if any(e["outcome"] in ("tentative", "rolled_back") for e in attempts):
            lines.append("Attempts since the last committed program (round "
                         f"{attempts[-1].get('anchor_round')}); per-view numbers compare each "
                         "attempt with that committed program:")
        elif all(e["outcome"] != "kept" for e in attempts):
            lines.append("Previous attempts from this same program (none was kept; the program "
                         "below is unchanged):")
        else:
            lines.append("What your last edit did:")
        for e in attempts:
            change = e.get("change") or "(no CHANGE line)"
            lines += ["", f"Attempt in round {e['round']} — you said: "
                          f"\"{e.get('tag') or '?'} - {change}\""]
            if e.get("diff"):
                lines.append("  diff (- removed, + added):")
                lines += ["    " + l for l in e["diff"]]
            lines.append("  result: " + _reason_text(e))
            if e.get("delta"):
                lines += ["  " + l for l in _delta_table(e["delta"], signal)]
                d = e["delta"]
                unit = "lower depth error" if signal == "depth" else "IoU"
                if d["worst_change"] < -5e-4:          # nothing to point at for a no-op edit
                    lines.append(f"  worst: {d['worst_view']} {unit} {d['worst_change']:+.3f}, "
                                 f"{_MOSTLY[d['mostly']]}")
        if effect_image:
            lines += ["", f"Image {effect_image} shows what the attempt in round "
                          f"{attempts[-1]['round']} changed, view by view: GREEN = pixels it "
                          "fixed, RED = pixels it broke, GREY = right before and after, pale = "
                          "wrong before and after."]
        lines += ["", FEEDBACK_RULE]
    if history:
        lines += ["", "Round history so far:"] + [f"- {h}" for h in history]
    return "\n".join(lines) if lines else None


def branch_text(branch_rounds, anchor_round, rounds_left, diff):
    """`--patience`: the current program is an uncommitted branch (ABLATION_PLAN F)."""
    lines = [f"Your edit in round {branch_rounds[-1]} did not beat the last committed program "
             f"(round {anchor_round}): it lowered the geometric score or broke a view. It is kept "
             f"TENTATIVELY for {rounds_left} more round(s): your next edit is committed only if "
             f"it beats round {anchor_round}'s program, otherwise the branch is rolled back. "
             "Continue in this direction only if you believe it leads to a better shape; "
             "otherwise revert it."]
    if diff:
        lines += [f"The branch so far, vs round {anchor_round}'s program (- removed, + added):"]
        lines += ["    " + l for l in diff]
    return "\n".join(lines)


def repeat_prompt(round_):
    return (f"That program is the same as your attempt in round {round_}, which was not kept "
            "(see the previous attempts above), so it was not built. Propose a different "
            "change: reply with a CHANGE line and the complete revised program in one "
            "```python block.")


def repair_prompt(error):
    return ("That program failed:\n" + error.strip() + "\n\nFix it and reply with the complete "
            "corrected program in one ```python block.")


VLM_JUDGE = """Image 1 is the TARGET part. Image 2 is reconstruction A. Image 3 is \
reconstruction B. All three are rendered by the same 4 cameras.
{views}

Which reconstruction matches the TARGET's shape more closely (overall form, size, \
holes, steps, cut-outs)? Think briefly, then end your reply with a last line that is \
exactly `KEEP A` or `KEEP B`."""


def parse_judgement(text: str) -> str | None:
    m = re.findall(r"KEEP\s+([AB])\b", text.upper())
    return m[-1] if m else None


# --------------------------------------------- verification questions (CADCodeVerify)
QUESTIONS_MARK = "Write verification questions"
ANSWER_MARK = "Answer each question about the part"
FEEDBACK_MARK = "Turn these answers into corrections"

QUESTIONS_PROMPT = QUESTIONS_MARK + """ for this TARGET part.
{views}

Write between 2 and 5 yes/no questions that any correct reconstruction of this part must \
answer with "Yes": about its overall form, the number and placement of holes, slots, \
steps, bosses and cut-outs, symmetry and proportions. Only ask what the pictures clearly \
show. Reply with a numbered list of questions and nothing else.

Examples for other parts:
1. Is the part an L-shaped bracket with two perpendicular plates?
2. Does the vertical plate have exactly two round through-holes?
3. Is the base plate about twice as long as it is wide?

1. Is the part a cylinder with a flange at its lower end?
2. Are there four holes evenly spaced around the flange?"""

ANSWER_PROMPT = ANSWER_MARK + """ shown in the picture.
{views}

Remember that the 4 images are all of the same object from different angles. The answer \
to each question must be one of "Yes", "No" or "Unclear". Answer "Unclear" when you are \
unsure or the pictures do not show enough. Give reasoning for every answer, in this format:

1. **Question?**
- **Answer:** Yes/No/Unclear
- **Reasoning:** ...

Questions:
{questions}"""

FEEDBACK_PROMPT = FEEDBACK_MARK + """ for the 3D reconstruction.
These questions about the target part were answered on renders of our current \
reconstruction:
{qa}

Summarise them as practical corrections to the part, in a few specific sentences:
(1) after the corrections every question must be answered "Yes";
(2) do not change anything that would turn a "Yes" answer into "No";
(3) only address the "No" and "Unclear" answers;
(4) do not comment on the image quality or the camera angles."""


def parse_questions(text: str) -> list[str]:
    qs = [m.group(1).strip() for m in re.finditer(r"^\s*\d+[.)]\s*\**(.+?\?)\**\s*$", text, re.M)]
    seen, out = set(), []
    for q in qs:
        if q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out[:5]


def parse_answers(text: str, n: int) -> list[str]:
    """-> one of "yes" / "no" / "unclear" per question (missing -> "unclear")."""
    found = re.findall(r"\*{0,2}Answer:?\*{0,2}:?\s*\**\s*(Yes|No|Unclear)", text, re.I)
    ans = [a.lower() for a in found[:n]]
    return ans + ["unclear"] * (n - len(ans))


def qa_text(questions, answers, only_failed=False):
    return "\n".join(f"{i}. {q} -> {a.capitalize()}"
                     for i, (q, a) in enumerate(zip(questions, answers), 1)
                     if not only_failed or a != "yes")
