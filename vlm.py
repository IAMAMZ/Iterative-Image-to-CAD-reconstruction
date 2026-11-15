"""Talk to a local vision-language model through Ollama, and the prompts the agent uses.

Needs `ollama serve` running and a model that can see images (e.g. gemma4:12b).
No API keys; everything stays on this machine.
"""
import base64
import json
import re
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"


def chat(messages, model="gemma4:12b", think=False, temperature=0.4, num_ctx=16384,
         max_tokens=2500, deadline=480):
    """messages: [{"role", "content", "images": [png bytes, ...]}] -> (reply text, stats).

    Streams the reply so a model stuck repeating itself is cut off after `max_tokens`
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


# ------------------------------------------------------------------ prompts
SYSTEM = """You are a CAD engineer. You write CadQuery (Python) programs that rebuild a \
mechanical part from pictures of it.

Rules for every program you write:
- Units are millimetres. Z is up.
- Start with `import cadquery as cq` (you may also `import math`; nothing else).
- Assign the final single solid to a variable named `result`.
- Reply with exactly one ```python code block containing the whole program.

Coordinate frames of the workplanes:
- cq.Workplane("XY"): local x = +X, local y = +Y, extrudes towards +Z.
- cq.Workplane("XZ"): local x = +X, local y = +Z, extrudes towards -Y (use both=True to centre on Y=0).
- cq.Workplane("YZ"): local x = +Y, local y = +Z, extrudes towards +X.

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

Example:
```python
import cadquery as cq

base = cq.Workplane("XY").box(60, 40, 8, centered=(True, True, False))
boss = cq.Workplane("XY").workplane(offset=8).circle(10).extrude(12)
result = base.union(boss).faces(">Z").workplane().hole(8)
result = result.faces("<Z").workplane().rarray(44, 24, 2, 2).hole(5)
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
            f"{size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm (X x Y x Z). "
            f"Its exact position does not matter; only shape and size are compared.")


def initial_prompt(lo, hi):
    return (f"Here is the target part.\n{VIEWS_TEXT}\n\n{bbox_text(lo, hi)}\n\n"
            "Look at the main body first (plate, block, L-shape, cylinder, steps), then "
            "holes, slots, cut-outs and fillets. Write a CadQuery program that rebuilds it.")


def refine_prompt(arm, program, lo, hi, cand_size=None, residual_table=None):
    lines = [
        "Image 1 is the TARGET part. Image 2 is our CURRENT reconstruction, rendered by the "
        "same 4 cameras.", VIEWS_TEXT, "", bbox_text(lo, hi),
    ]
    if cand_size is not None:
        lines.append("The current reconstruction's bounding box is "
                     f"{cand_size[0]:.1f} x {cand_size[1]:.1f} x {cand_size[2]:.1f} mm.")
    if arm == "geo":
        lines += [
            "",
            "Image 3 is the silhouette residual for the same 4 views: GREY = correct, "
            "RED = material the target has but we are MISSING, BLUE = EXTRA material we "
            "have but the target does not.",
            "Image 4 is the depth error where both cover the pixel: pale = correct, "
            "dark red/purple = surface at the wrong depth (wrong thickness or height).",
            "Per-view numbers (IoU 1.0 = perfect outline; all 8 cameras):",
            residual_table,
        ]
    lines += [
        "", "Current program:", f"```python\n{program.strip()}\n```", "",
        "Find the single biggest geometric difference between the target and the current "
        "reconstruction, say in one sentence what it is, then reply with the complete "
        "revised program in one ```python block.",
    ]
    return "\n".join(lines)


def repair_prompt(error):
    return ("That program failed:\n" + error.strip() + "\n\nFix it and reply with the complete "
            "corrected program in one ```python block. Use only the CadQuery methods listed.")


VLM_JUDGE = """Image 1 is the TARGET part. Image 2 is reconstruction A. Image 3 is \
reconstruction B. All three are rendered by the same 4 cameras.
{views}

Which reconstruction matches the TARGET's shape more closely (overall form, size, \
holes, steps, cut-outs)? Think briefly, then end your reply with a last line that is \
exactly `KEEP A` or `KEEP B`."""


def parse_judgement(text: str) -> str | None:
    m = re.findall(r"KEEP\s+([AB])\b", text.upper())
    return m[-1] if m else None
