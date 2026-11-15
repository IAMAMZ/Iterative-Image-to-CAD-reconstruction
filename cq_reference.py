"""Short CadQuery reference entries, picked per prompt, for a small local model.

The full CadQuery docs are far too long for a 7B model's prompt, so each prompt gets only the
entries that matter: the methods the current program uses (plus the Workplane/Sketch switch),
and for a repair the method that failed and its correct alternatives.

Every entry = the real signature, read from the installed CadQuery with `inspect` (so it
can never name a method or argument that does not exist), plus a hand-written one-line rule
and an example. tests/test_cq_reference.py runs every example.

    from cq_reference import for_program, for_error
    text = for_program(src)            # "CadQuery reference ..." block, or ""
    text = for_error(error, src)
"""
import ast
import inspect
import re

import cadquery as cq

OWNERS = {"Workplane": cq.Workplane, "Sketch": cq.Sketch, "Shape": cq.Shape}
SKIP_PARAMS = {"self", "tag", "forConstruction", "clean", "combine", "ignore_selection"}
MAX_ENTRIES = 12

HEADER = """CadQuery reference (signatures from the installed CadQuery; use only these forms):
Two kinds of objects: a Workplane builds 3D solids; wp.sketch() opens a 2D Sketch, and
.finalize() closes it and returns to the Workplane. Inside sketch() ... finalize() only Sketch
methods work; Workplane methods (moveTo, box, hole, cutBlind, fillet, ...) only outside."""

# "Owner.method": (rule, example). Examples are complete expressions that build a solid.
ENTRIES = {
    # --- Workplane: 3D
    "Workplane.workplane": (
        "new workplane parallel to the current one; offset moves it along its normal",
        'cq.Workplane("XY").box(40, 40, 10).faces(">Z").workplane(offset=0).circle(5).extrude(8)'),
    "Workplane.sketch": (
        "open a 2D sketch on this workplane; must end with .finalize() before extrude",
        'cq.Workplane("XY").sketch().rect(40, 20).finalize().extrude(5)'),
    "Workplane.moveTo": (
        "Workplane only (not inside a sketch): move to (x, y) on the workplane before box/circle/rect",
        'cq.Workplane("XY").moveTo(10, 5).box(20, 10, 4)'),
    "Workplane.box": (
        "THREE sizes, all > 0: box(length_x, width_y, height_z); centred on the point by default",
        'cq.Workplane("XY").box(40, 20, 10)'),
    "Workplane.cylinder": (
        "cylinder(height, radius) along the workplane normal, centred on the point",
        'cq.Workplane("XY").cylinder(20, 5)'),
    "Workplane.rect": (
        "2D rectangle on a Workplane, to extrude or cutBlind next",
        'cq.Workplane("XY").rect(30, 10).extrude(4)'),
    "Workplane.circle": (
        "2D circle on a Workplane, radius first",
        'cq.Workplane("XY").circle(8).extrude(10)'),
    "Workplane.polyline": (
        "2D polygon through points; call .close() before extrude",
        'cq.Workplane("XY").polyline([(0, 0), (30, 0), (0, 20)]).close().extrude(5)'),
    "Workplane.extrude": (
        "turn the pending 2D shape into a solid; negative = the other direction",
        'cq.Workplane("XY").rect(20, 20).extrude(-6)'),
    "Workplane.revolve": (
        "revolve the pending 2D shape around an axis given by two points on the workplane",
        'cq.Workplane("XZ").moveTo(10, 0).rect(4, 10).revolve(360, (0, 0, 0), (0, 1, 0))'),
    "Workplane.pushPoints": (
        "put several points on the stack; the next circle/hole/box is made at each",
        'cq.Workplane("XY").box(60, 40, 5).faces(">Z").workplane().pushPoints([(-20, 0), (20, 0)]).hole(6)'),
    "Workplane.hole": (
        "drill through the whole solid at the current point(s): select a face and workplane first",
        'cq.Workplane("XY").box(40, 40, 10).faces(">Z").workplane().hole(8)'),
    "Workplane.cutBlind": (
        "cut the 2D shape drawn JUST BEFORE it into the solid (negative = into the part); "
        "without one you get 'No pending wires present'",
        'cq.Workplane("XY").box(40, 40, 10).faces(">Z").workplane().rect(20, 10).cutBlind(-4)'),
    "Workplane.cutThruAll": (
        "like cutBlind, but through the whole part",
        'cq.Workplane("XY").box(40, 40, 10).faces(">Z").workplane().rect(10, 10).cutThruAll()'),
    "Workplane.fillet": (
        "round the SELECTED edges: select them first with .edges(...); radius smaller than the edge's faces",
        'cq.Workplane("XY").box(40, 40, 10).edges("|Z").fillet(3)'),
    "Workplane.chamfer": (
        "bevel the SELECTED edges: select them first with .edges(...)",
        'cq.Workplane("XY").box(40, 40, 10).edges(">Z").chamfer(1)'),
    "Workplane.faces": (
        'select faces: ">Z" top, "<Z" bottom, ">X", "<Y", ...; follow with .workplane() to draw on it',
        'cq.Workplane("XY").box(40, 40, 10).faces(">Z").workplane().circle(5).extrude(5)'),
    "Workplane.edges": (
        'select edges: "|Z" parallel to Z, ">Z" on the top, ...; used before fillet/chamfer',
        'cq.Workplane("XY").box(40, 40, 10).edges("|Z").fillet(2)'),
    "Workplane.union": (
        "add another solid (a separate Workplane expression)",
        'cq.Workplane("XY").box(40, 40, 10).union(cq.Workplane("XY").cylinder(30, 5))'),
    "Workplane.cut": (
        "subtract another solid (a separate Workplane expression)",
        'cq.Workplane("XY").box(40, 40, 10).cut(cq.Workplane("XY").cylinder(30, 5))'),
    "Workplane.translate": (
        "move the whole solid by (dx, dy, dz)",
        'cq.Workplane("XY").box(10, 10, 10).translate((5, 0, 0))'),
    "Workplane.rotate": (
        "rotate around the axis through two points, angle in degrees",
        'cq.Workplane("XY").box(30, 10, 5).rotate((0, 0, 0), (0, 0, 1), 45)'),
    # --- Sketch: 2D, between .sketch() and .finalize()
    "Sketch.segment": (
        "straight edge; the first call takes two points, later calls one point (continues the edge)",
        'cq.Workplane("XY").sketch().segment((0, 0), (30, 0)).segment((30, 20)).segment((0, 20))'
        '.close().assemble().finalize().extrude(5)'),
    "Sketch.arc": (
        "arc through three points (start, middle, end); later calls may give (middle, end)",
        'cq.Workplane("XY").sketch().segment((0, 0), (30, 0)).arc((40, 10), (30, 20)).segment((0, 20))'
        '.close().assemble().finalize().extrude(5)'),
    "Sketch.close": (
        "close the edge loop back to its start; then .assemble() turns the edges into a face",
        'cq.Workplane("XY").sketch().segment((0, 0), (20, 0)).segment((0, 20)).close().assemble()'
        '.finalize().extrude(3)'),
    "Sketch.assemble": (
        "turn the closed edges drawn with segment/arc into a face",
        'cq.Workplane("XY").sketch().segment((0, 0), (20, 0)).segment((0, 20)).close().assemble()'
        '.finalize().extrude(3)'),
    "Sketch.push": (
        "set location(s) inside a sketch; the next circle/rect is placed there (Sketch's moveTo)",
        'cq.Workplane("XY").sketch().rect(60, 30).push([(-15, 0), (15, 0)]).circle(4, mode="s")'
        '.finalize().extrude(5)'),
    "Sketch.circle": (
        "circle face, radius positionally: circle(r) adds, circle(r, mode='s') subtracts a hole",
        'cq.Workplane("XY").sketch().circle(20).circle(8, mode="s").finalize().extrude(5)'),
    "Sketch.rect": (
        "rectangle face (centred); mode='s' subtracts",
        'cq.Workplane("XY").sketch().rect(40, 20).rect(10, 5, mode="s").finalize().extrude(5)'),
    "Sketch.reset": (
        "clear the current selection/locations so the next shape is placed at the origin again",
        'cq.Workplane("XY").sketch().push([(10, 0)]).circle(3).reset().rect(40, 20)'
        '.finalize().extrude(4)'),
    "Sketch.face": (
        "add (or with mode='s' subtract) the face of another sketch",
        'cq.Workplane("XY").sketch().rect(40, 20).face(cq.Sketch().circle(5), mode="s")'
        '.finalize().extrude(4)'),
    "Sketch.finalize": (
        "close the sketch and return to the Workplane (then extrude / cutBlind)",
        'cq.Workplane("XY").sketch().rect(10, 10).finalize().extrude(2)'),
    # --- Shape
    "Shape.scale": (
        "scale a solid about the origin: cq.Workplane(obj=result.val().scale(f)) (Workplane has no .scale)",
        'cq.Workplane(obj=cq.Workplane("XY").box(10, 10, 10).val().scale(1.5))'),
}

# methods that do not exist on one kind of object -> what to use there instead
WRONG_OWNER = {
    ("Sketch", "moveTo"): ["Sketch.push", "Sketch.circle", "Sketch.rect"],
    ("Sketch", "center"): ["Sketch.push"],
    ("Sketch", "pushPoints"): ["Sketch.push"],
    ("Sketch", "extrude"): ["Sketch.finalize", "Workplane.extrude"],
    ("Sketch", "hole"): ["Sketch.circle", "Sketch.finalize"],
    ("Sketch", "box"): ["Sketch.rect", "Sketch.finalize"],
    ("Sketch", "workplane"): ["Sketch.finalize", "Workplane.workplane"],
    ("Workplane", "scale"): ["Shape.scale"],
    ("Workplane", "segment"): ["Workplane.sketch", "Sketch.segment"],
    ("Workplane", "arc"): ["Workplane.sketch", "Sketch.arc"],
    ("Workplane", "assemble"): ["Workplane.sketch", "Sketch.assemble"],
    ("Workplane", "push"): ["Workplane.pushPoints"],
}
# a failing method -> the entries needed to use it correctly
NEEDS = {
    "cutBlind": ["Workplane.faces", "Workplane.rect"],
    "cutThruAll": ["Workplane.faces", "Workplane.rect"],
    "fillet": ["Workplane.edges"],
    "chamfer": ["Workplane.edges"],
    "hole": ["Workplane.faces", "Workplane.pushPoints"],
    "extrude": ["Workplane.sketch", "Sketch.finalize"],
}


def signature(key: str) -> str:
    """'Workplane.box' -> 'Workplane.box(length, width, height, centered=True)'."""
    owner, name = key.split(".")
    sig = inspect.signature(getattr(OWNERS[owner], name))
    parts = []
    for p in sig.parameters.values():
        if p.name in SKIP_PARAMS or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is p.empty:
            parts.append(p.name)
        else:
            d = p.default
            d = repr(d) if isinstance(d, (int, float, str, bool, type(None), tuple)) else "..."
            parts.append(f"{p.name}={d}")
    return f"{key}({', '.join(parts)})"


def entry(key: str) -> str:
    rule, example = ENTRIES[key]
    return f"- {signature(key)}\n    {rule}\n    e.g. {example}"


def methods_used(src: str) -> list[str]:
    """['Workplane.sketch', 'Sketch.segment', ...] in order of first use, by following each
    call chain: methods after .sketch() and before .finalize() belong to the Sketch."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    seen = []

    def walk(node):
        """-> 'Workplane' | 'Sketch' | None: the kind of object this expression gives."""
        if isinstance(node, ast.Call):
            for a in list(node.args) + [k.value for k in node.keywords]:
                walk(a)
            f = node.func
            if isinstance(f, ast.Attribute):
                if isinstance(f.value, ast.Name) and f.value.id == "cq":
                    return {"Workplane": "Workplane", "Sketch": "Sketch"}.get(f.attr)
                owner = walk(f.value) or "Workplane"   # variables are mostly workplanes
                key = f"{owner}.{f.attr}"
                if key not in seen:
                    seen.append(key)
                if f.attr == "sketch":
                    return "Sketch"
                if f.attr == "finalize":
                    return "Workplane"
                if owner == "Workplane" and f.attr == "val":
                    return "Shape"
                return owner
        elif isinstance(node, ast.Attribute):
            walk(node.value)
        for child in ast.iter_child_nodes(node) if not isinstance(node, ast.Call) else []:
            walk(child)
        return None

    for st in tree.body:
        walk(st)
    return seen


def _block(keys):
    keys = [k for k in dict.fromkeys(keys) if k in ENTRIES][:MAX_ENTRIES]
    if not keys:
        return ""
    return HEADER + "\n" + "\n".join(entry(k) for k in keys)


def for_program(src: str) -> str:
    """Reference for an edit prompt: the Workplane/Sketch switch and every listed method the
    current program uses."""
    used = methods_used(src)
    core = ["Workplane.sketch", "Sketch.finalize"] if "Workplane.sketch" in used else []
    return _block(core + used)


_FAILED_OP = re.compile(r"\] step +\d+ \(line \d+\) (\w+)\(")
_NO_ATTR = re.compile(r"'(Workplane|Sketch)' object has no attribute '(\w+)'")
_BAD_CALL = re.compile(r"(Workplane|Sketch)\.(\w+)\(\) (?:got an|missing|takes)")


def for_error(error: str, src: str | None = None) -> str:
    """Reference for a repair prompt: the entries for the method that failed and what it
    needs (or, for a method that does not exist on that object, what to use instead)."""
    keys = []
    m = _NO_ATTR.search(error)
    if m:
        keys += WRONG_OWNER.get((m.group(1), m.group(2)), [])
    m = _BAD_CALL.search(error)
    if m:
        keys.append(f"{m.group(1)}.{m.group(2)}")
    m = _FAILED_OP.search(error)
    if m and m.group(1) != "program":
        name = m.group(1)
        used = methods_used(src or "")
        owner = next((k.split(".")[0] for k in used if k.endswith("." + name)), "Workplane")
        keys += [f"{owner}.{name}"] + NEEDS.get(name, [])
    return _block(keys)
