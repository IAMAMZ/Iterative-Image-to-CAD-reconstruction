"""Talk to the agent's vision-language model, and the prompts the agent uses.

Backends (pick with `backend=`):
  ollama  a local open-weight VLM through `ollama serve` (e.g. gemma4:12b); no API keys
  echo    a fake agent for tests and dry runs: it perturbs one number of the current
          program, answers judge/question prompts deterministically, never calls a model
Every backend returns (reply text, stats) with token counts, so runs can be costed.
A proprietary backend (Gemini / Vertex AI) plugs in as one more function in BACKENDS.
"""
import ast
import base64
import builtins
import hashlib
import json
import random
import re
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"


# ------------------------------------------------------------------ backends
def _ollama(messages, model, think, temperature, num_ctx, max_tokens, deadline):
    """Streams the reply so a model stuck repeating itself is cut off after `max_tokens`
    tokens or `deadline` seconds, whichever comes first (stats["cut_off"] says which)."""
    msgs = []
    for m in messages:
        m = dict(m)
        if m.get("images"):
            m["images"] = [base64.b64encode(b).decode() for b in m["images"]]
        msgs.append(m)
    body = {"model": model, "messages": msgs, "stream": True, "think": think,
            "options": {"temperature": temperature, "num_ctx": num_ctx,
                        "num_predict": max_tokens, "repeat_penalty": 1.1}}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    parts, last, cut = [], {}, None
    with urllib.request.urlopen(req, timeout=deadline) as r:
        for line in r:
            if not line.strip():
                continue
            last = json.loads(line)
            parts.append(last.get("message", {}).get("content", ""))
            if last.get("done"):
                if last.get("done_reason") == "length":
                    cut = "max_tokens"
                break
            if time.time() - t0 > deadline:
                cut = "deadline"
                break  # closing the connection makes Ollama stop generating
    stats = {"seconds": round(time.time() - t0, 1),
             "prompt_tokens": last.get("prompt_eval_count"),
             "output_tokens": last.get("eval_count"), "cut_off": cut}
    return "".join(parts), stats


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


BACKENDS = {"ollama": _ollama, "echo": _echo}


def chat(messages, model="gemma4:12b", think=False, temperature=0.4, num_ctx=16384,
         max_tokens=2500, deadline=480, backend="ollama"):
    """messages: [{"role", "content", "images": [png bytes, ...]}] -> (reply text, stats)."""
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend!r}; choose from {sorted(BACKENDS)}")
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


_BREAK_BEFORE = (".union(", ".cut(", ".intersect(", ".extrude(", ".sketch(", ".push(",
                 ".finalize(", ".workplane(")


def format_program(src: str, width=100) -> str:
    """Display only: break long one-line method chains (cadrille writes whole parts on one
    line) into one call per line inside parentheses. The result is checked to parse to the
    same AST; if anything is off the original text is returned unchanged."""
    out = []
    for line in src.splitlines():
        m = re.match(r"^(\s*)([A-Za-z_]\w*)\s*=\s*(.+)$", line)
        if not m or len(line) <= width:
            out.append(line)
            continue
        indent, name, expr = m.groups()
        pieces, depth, start, i, quote = [], 0, 0, 0, None
        while i < len(expr):
            ch = expr[i]
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif depth == 0 and any(expr.startswith(b, i) for b in _BREAK_BEFORE) and i > start:
                pieces.append(expr[start:i])
                start = i
            i += 1
        pieces.append(expr[start:])
        if len(pieces) == 1:
            out.append(line)
            continue
        pad = indent + " " * (len(name) + 4)
        out.append(f"{indent}{name} = (" + pieces[0] + "".join("\n" + pad + p for p in pieces[1:]) + ")")
    new = "\n".join(out) + ("\n" if src.endswith("\n") else "")
    try:
        if ast.dump(ast.parse(new)) != ast.dump(ast.parse(src)):
            return src
    except SyntaxError:
        return src
    return new


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


_BUILTINS = set(dir(builtins))


def _definitions(tree):
    """Top-level `name = ...` statements of a module, in order: {name: stmt}."""
    defs = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            defs.setdefault(st.targets[0].id, st)
    return defs


def _loaded(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def undefined_names(src: str) -> set[str]:
    """Names a program reads but never assigns or imports (None if it does not parse)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            bound |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, (ast.FunctionDef, ast.Lambda)):
            bound |= {a.arg for a in n.args.args}
            if isinstance(n, ast.FunctionDef):
                bound.add(n.name)
    return _loaded(tree) - bound - _BUILTINS


def restore_definitions(src: str, base: str | None):
    """Small models often copy an edited program without the lines that define the
    workplanes it uses (cadrille's `w0 = cq.Workplane(...)`), so it fails with NameError.
    Put back, right after the imports, every top-level definition from the program being
    edited (`base`) that the new program uses but does not define, plus whatever those
    definitions need in turn. -> (program, [restored names])."""
    if not base:
        return src, []
    missing = undefined_names(src)
    if not missing:
        return src, []
    try:
        base_tree = ast.parse(base)
    except SyntaxError:
        return src, []
    defs = _definitions(base_tree)
    need, todo = set(), [m for m in missing if m in defs]
    while todo:
        name = todo.pop()
        if name in need:
            continue
        need.add(name)
        todo += [d for d in _loaded(defs[name].value) if d in defs and d not in need]
    if not need:
        return src, []
    order = [n for n in defs if n in need]                      # keep the base program's order
    block = "\n".join(ast.get_source_segment(base, defs[n]) for n in order)
    lines = src.splitlines()
    at = 0
    for i, l in enumerate(lines):                               # after the last leading import
        if l.startswith(("import ", "from ")):
            at = i + 1
        elif l.strip() and not l.startswith("#"):
            break
    out = lines[:at] + ["# restored from the current program (the reply used but did not define it)",
                        block] + lines[at:]
    return "\n".join(out) + "\n", order


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
- Do not throw the program away and remodel the part from generic boxes and cylinders.
- Do not add features the pictures do not show, and do not remove features they do show.
- Start your reply with one line `CHANGE: <structural|dimensional|positional> - <what you \
change, one sentence>`, then the code block. If nothing worthwhile is left to fix, reply \
with exactly `NO_CHANGE` and no code.

Coordinate frames of the workplanes:
- cq.Workplane("XY"): local x = +X, local y = +Y, extrudes towards +Z.
- cq.Workplane("XZ"): local x = +X, local y = +Z, extrudes towards -Y (use both=True to centre on Y=0).
- cq.Workplane("YZ"): local x = +Y, local y = +Z, extrudes towards +X.
- cq.Workplane("XY", origin=(x, y, z)) moves the workplane's origin.

CadQuery methods you can use (only real ones; do not invent methods):
  .box(x, y, z, centered=(True, True, False))   .cylinder(height, radius)
  .rect(w, h)  .circle(r)  .polyline([(x, y), ...]).close()  .slot2D(length, diameter)
  .extrude(distance, both=False)   .revolve(360, (0, 0, 0), (0, 1, 0))
  .center(x, y)   .moveTo(x, y)   .pushPoints([(x, y), ...])
  .rarray(x_spacing, y_spacing, nx, ny)   .polarArray(radius, 0, 360, count)
  .hole(diameter)   .cboreHole(d, cbore_d, cbore_depth)   .cutBlind(-depth)   .cutThruAll()
  .faces(">Z").workplane()   .edges("|Z").fillet(r)   .edges(">Z").chamfer(d)
  .translate((x, y, z))   .rotate((0, 0, 0), (0, 0, 1), angle_deg)
  .union(other)   .cut(other)   .intersect(other)
Sketch API (2D profiles, as in the programs you will be given):
  wp.sketch().segment((x0, y0), (x1, y1)).segment((x2, y2)).arc((xm, ym), (x3, y3)).close()
    .assemble()   .push([(x, y), ...]).circle(r, mode='s')   .rect(w, h, mode='s')
    .finalize().extrude(depth)          (mode='s' subtracts, the default mode adds)
  cq.Workplane(obj=shape.val().scale(f)) rescales a whole solid about the origin.

Example:
```python
import cadquery as cq

base = cq.Workplane("XY").box(120, 80, 16, centered=(True, True, False))
boss = cq.Workplane("XY").workplane(offset=16).circle(20).extrude(24)
result = base.union(boss).faces(">Z").workplane().hole(16)
result = result.faces("<Z").workplane().rarray(88, 48, 2, 2).hole(10)
```
"""

VIEWS_TEXT = """The picture is a 2x2 grid of the same part seen by 4 calibrated cameras:
- top-left "front": looking along +Y; image right = +X, image up = +Z
- top-right "right": looking along -X; image right = +Y, image up = +Z
- bottom-left "top": looking down -Z; image right = +X, image up = +Y
- bottom-right "iso_fr": from the front-right, above"""


def bbox_text(lo, hi):
    size = [h - l for l, h in zip(lo, hi)]
    return (f"Measured from the calibrated depth maps, the part's bounding box is about "
            f"{size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} units (X x Y x Z). "
            f"Its exact position does not matter; only shape and size are compared.")


def initial_prompt(lo, hi):
    return (f"Here is the target part.\n{VIEWS_TEXT}\n\n{bbox_text(lo, hi)}\n\n"
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


def refine_prompt(program, lo, hi, cand_size=None, *, n_images=2, residual_table=None,
                  detail=False, kernel=None, qa_feedback=None, gsolver=None, reference=None):
    """The edit request. Which evidence goes in is decided by the arm (see refine.ARMS)."""
    lines = []
    if n_images:
        lines += ["Image 1 is the TARGET part. Image 2 is our CURRENT reconstruction, rendered "
                  "by the same 4 cameras.", VIEWS_TEXT]
    lines += ["", bbox_text(lo, hi)]
    if cand_size is not None:
        lines.append("The current reconstruction's bounding box is "
                     f"{cand_size[0]:.1f} x {cand_size[1]:.1f} x {cand_size[2]:.1f} units.")
    if residual_table is not None:
        k = 3
        if n_images >= 4:
            lines += ["",
                      "Image 3 is the silhouette residual for the same 4 views: GREY = correct, "
                      "RED = material the target has but we are MISSING, BLUE = EXTRA material we "
                      "have but the target does not.",
                      "Image 4 is the depth error where both cover the pixel: pale = correct, "
                      "dark red/purple = surface at the wrong depth (wrong thickness or height)."]
            k = 5
        if detail:
            lines.append(f"Image {k} zooms into the largest residual: target | current | residual.")
        lines += ["Per-view numbers from all 8 cameras (IoU 1.0 = perfect outline; weight = how "
                  "much that camera is trusted, views that disagree with the others count less):",
                  residual_table]
    if kernel:
        lines += ["", "CAD kernel report for the current program:", kernel]
    if qa_feedback:
        lines += ["", "Visual verification of the current reconstruction found these problems:",
                  qa_feedback]
    if gsolver:
        lines += ["", "Geometric properties, target vs current:", gsolver]
    if reference:
        lines += ["", reference]
    lines += ["", "Current program:", f"```python\n{format_program(program).strip()}\n```", "",
              "Find the single biggest geometric difference between the target and the current "
              "reconstruction, fix it, and reply in the format from the rules (CHANGE line, then "
              "the complete revised program in one ```python block), or NO_CHANGE."]
    return "\n".join(lines)


_NAME_ERROR = re.compile(r"NameError: name '(\w+)' is not defined")

# Sketch vs Workplane mix-ups seen in the pilot (qwen2.5vl:7b): error pattern -> how to fix it
API_HINTS = [
    (r"'Sketch' object has no attribute 'extrude'",
     "A sketch must be closed with .finalize() before extruding: "
     "wp.sketch()....finalize().extrude(depth)."),
    (r"'Sketch' object has no attribute '(moveTo|center|pushPoints|hole|box|cylinder|workplane)'",
     "Inside .sketch() ... .finalize() only Sketch methods work: place shapes with "
     ".push([(x, y)]) then .circle(r) / .rect(w, h) (mode='s' to subtract). Workplane methods "
     "such as moveTo/center/pushPoints/hole come after .finalize()."),
    (r"Sketch\.circle\(\) got an unexpected keyword argument",
     "Sketch.circle takes the radius positionally: .circle(r) or .circle(r, mode='s')."),
    (r"'Workplane' object has no attribute 'scale'",
     "Scale a whole solid with cq.Workplane(obj=result.val().scale(f)), not result.scale(f)."),
    (r"'Workplane' object has no attribute '(segment|arc|assemble)'",
     "segment/arc/assemble are Sketch methods: start with wp.sketch() and end with .finalize()."),
]


def repair_prompt(error, base=None, repeated=False, reference=None):
    """Build-error feedback. For an undefined name the current program defines, quote its
    definition; if the reply was a copy of the previous failed one, say so."""
    lines = ["That program failed:", error.strip()]
    m = _NAME_ERROR.search(error)
    if m and base:
        try:
            d = _definitions(ast.parse(base)).get(m.group(1))
        except SyntaxError:
            d = None
        if d is not None:
            lines += ["", f"`{m.group(1)}` is defined in the current program as:",
                      f"```python\n{ast.get_source_segment(base, d)}\n```",
                      "Include that line (and the import) in your program."]
        else:
            lines += ["", f"`{m.group(1)}` is used but never defined: define it before use."]
    for pat, hint in API_HINTS:
        if re.search(pat, error):
            lines += ["", "How to fix it: " + hint]
            break
    if reference:
        lines += ["", reference]
    if repeated:
        lines += ["", "Your reply was identical to the previous failed program. Change the code "
                      "so that this error cannot happen again."]
    lines += ["", "Fix it and reply with the complete corrected program in one ```python block. "
                  "Use only the CadQuery methods listed."]
    return "\n".join(lines)


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
