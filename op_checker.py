"""Check every CadQuery operation as it runs, and log the illegal ones.

A model (e.g. a VLA) sends CadQuery commands. Instead of only finding out at the end
that "the part is broken", this traces each Workplane operation (box, extrude, hole,
fillet, cut, ...), even inside one long chained statement, and after each one asks
the CAD kernel itself whether the result is legal:

  error    the kernel refused the operation (OpenCascade exception), or the result
           failed OpenCascade's own validity check (BRepCheck_Analyzer: self-
           intersecting sketch, open shell, bad orientation, ...), or it removed all
           material. Execution stops and IllegalOperation is raised.
  warning  legal but probably not what was meant: the operation changed nothing
           (a hole/cut that misses the part), a selector matched nothing, or the part
           fell apart into several pieces.
  ok       fine; the step still records the part's volume / solids / faces.

Every step is one JSON record (see OpTrace.steps), written as JSONL by generate_solid.py:
  {"step": 4, "op": "fillet", "call": "fillet(20)", "line": 3, "code": "...",
   "status": "error", "error_type": "StdFail_NotDone", "message": "BRep_API: command not done",
   "hint": "the fillet/chamfer is too big for the selected edges ...", "checks": [...]}

Only cq.Workplane methods are traced; code that calls the lower-level cq.Solid/cq.Face
API directly is still caught by the final check in generate_solid.check_solid.
"""
import inspect
from pathlib import Path

import cadquery as cq
from OCP.BRepCheck import BRepCheck_Analyzer, BRepCheck_Status
from OCP.TopAbs import (TopAbs_EDGE, TopAbs_FACE, TopAbs_SHELL, TopAbs_SOLID,
                        TopAbs_VERTEX, TopAbs_WIRE)
from OCP.TopExp import TopExp_Explorer

# Workplane methods that are plumbing, not modelling operations
NOT_TRACED = {"val", "vals", "all", "size", "first", "last", "item", "newObject", "findSolid",
              "findFace", "toOCC", "toSvg", "exportSvg", "export", "end", "tag", "ctx",
              "largestDimension", "add"}
# operations whose whole point is to change the part: warn if they leave it untouched
MODIFYING = {"cut", "union", "intersect", "hole", "cboreHole", "cskHole", "cutBlind",
             "cutThruAll", "fillet", "chamfer", "shell", "extrude", "revolve", "loft", "sweep",
             "twistExtrude", "combine", "split"}
SELECTORS = {"faces", "edges", "vertices", "wires", "solids", "shells", "compounds"}

# ---------------------------------------------------------------- hints
# (ops it applies to or None = any op, kernel error type or None = any) -> hint
EXCEPTION_HINTS = [
    ({"fillet", "chamfer"}, None,
     "the fillet/chamfer is too big for the selected edges (or they meet where it can't be "
     "built); use a smaller radius than half the thinnest wall, or select fewer edges"),
    ({"shell"}, None,
     "the shell wall is too thick for this part, or the chosen face can't be removed; "
     "use a thinner wall"),
    ({"extrude", "cutBlind", "twistExtrude", "revolve"}, "Standard_ConstructionError",
     "the extrude/revolve amount is zero or the sketch is degenerate; use a non-zero "
     "distance on a closed outline"),
    (None, "Standard_DomainError",
     "a size is zero or negative (or an argument is out of range); all dimensions must be > 0"),
    ({"loft", "sweep"}, None,
     "the profiles can't be joined: check they are closed, in order, and compatible"),
    (SELECTORS, "IndexError", "the selector asks for an item that doesn't exist (e.g. '>Z[5]' "
     "when there are fewer faces); use a smaller index"),
    (None, "StdFail_NotDone", "the CAD kernel could not build this operation with these values"),
    (None, "Standard_NullObject", "the operation got an empty shape: an earlier selection or "
     "sketch produced nothing"),
]
STATUS_HINTS = {
    "BRepCheck_SelfIntersectingWire": "a sketch outline crosses itself; reorder the points so "
                                      "the outline goes around without crossing",
    "BRepCheck_IntersectingWires": "two outlines in the same sketch cross each other",
    "BRepCheck_UnorientableShape": "the faces have no consistent inside/outside "
                                   "(usually caused by a self-crossing outline)",
    "BRepCheck_NotClosed": "an outline or surface is not closed; close the sketch with .close()",
    "BRepCheck_FreeEdge": "the surface has open edges, so it is not a closed solid",
    "BRepCheck_BadOrientation": "faces point the wrong way (inside/outside mixed up)",
    "BRepCheck_BadOrientationOfSubshape": "faces point the wrong way (inside/outside mixed up)",
    "BRepCheck_InvalidImbricationOfWires": "a hole outline is not inside its outer outline",
    "BRepCheck_EmptyWire": "a sketch outline has no edges",
    "BRepCheck_NotConnected": "the outline's edges don't join up end to end",
}
NO_EFFECT_HINT = ("the operation did not change the part: the feature probably misses it "
                  "(check its position, workplane, size and direction)")
EMPTY_SELECTION_HINT = ("the selector matched nothing, so the next operation has nothing to "
                        "work on; check the selector string (e.g. '>Z', '|Z')")


def exception_hint(op, error_type):
    for ops, etype, hint in EXCEPTION_HINTS:
        if (ops is None or op in ops) and (etype is None or etype == error_type):
            return hint
    return None


def brep_problems(shape):
    """OpenCascade's own validity check -> sorted list of problem names (empty = valid)."""
    an = BRepCheck_Analyzer(shape.wrapped)
    if an.IsValid():
        return []
    found = set()
    for kind in (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_WIRE, TopAbs_FACE, TopAbs_SHELL, TopAbs_SOLID):
        ex = TopExp_Explorer(shape.wrapped, kind)
        while ex.More():
            res = an.Result(ex.Current())
            if res is not None:
                found.update(s.name for s in res.Status() if s != BRepCheck_Status.BRepCheck_NoError)
                res.InitContextIterator()
                while res.MoreShapeInContext():
                    found.update(s.name for s in res.StatusOnShape()
                                 if s != BRepCheck_Status.BRepCheck_NoError)
                    res.NextShapeInContext()
            ex.Next()
    return sorted(found) or ["BRepCheck_Invalid"]


# ---------------------------------------------------------------- tracing
class IllegalOperation(Exception):
    """A traced CadQuery operation was refused by the kernel or produced an illegal shape."""

    def __init__(self, record):
        self.record = record
        where = f"line {record['line']}: " if record.get("line") else ""
        msg = f"{where}{record['call']} -> {record.get('error_type') or 'illegal'}: {record['message']}"
        if record.get("hint"):
            msg += f"  (hint: {record['hint']})"
        super().__init__(msg)


def _arg_repr(a):
    if isinstance(a, cq.Workplane):
        return "<Workplane>"
    if isinstance(a, cq.Shape):
        return f"<{type(a).__name__}>"
    return repr(a)


def _short_repr(args, kwargs, limit=80):
    parts = [_arg_repr(a) for a in args] + [f"{k}={_arg_repr(v)}" for k, v in kwargs.items()]
    s = ", ".join(parts)
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _solid_of(wp):
    """The solid a Workplane is currently working on, or None."""
    try:
        return wp.findSolid()
    except Exception:
        return None


def _result_solid(wp):
    """The solid an operation produced: what it left on the stack if that is a solid or
    compound (possibly an *empty* one, e.g. after cutting everything away), else the
    solid it inherited from earlier steps (sketching and selecting don't make one)."""
    made = [o for o in wp.objects if isinstance(o, (cq.Solid, cq.Compound))]
    if made:
        return made[0] if len(made) == 1 else cq.Compound.makeCompound(made)
    return _solid_of(wp)


def _same(a, b):
    """Same underlying B-rep solids (wrapper objects differ between calls)."""
    if a is None or b is None:
        return a is b
    sa, sb = a.Solids(), b.Solids()
    return len(sa) == len(sb) and all(x.wrapped.IsSame(y.wrapped) for x, y in zip(sa, sb)) \
        and (bool(sa) or a.wrapped.IsSame(b.wrapped))


def _geometry(shape):
    return {"n_solids": len(shape.Solids()), "n_faces": len(shape.Faces()),
            "volume": round(shape.Volume(), 6)}


class OpTrace:
    """Context manager: while active, every cq.Workplane operation is checked and logged.

        with OpTrace(program_path) as trace:
            runpy.run_path(program_path)
        trace.steps   # list of step records
    """

    def __init__(self, program=None):
        self.program = str(Path(program).resolve()) if program else None
        self.steps = []
        self._depth = 0
        self._saved = {}

    # -- where in the program was this op called from?
    def _caller(self):
        for fr in inspect.stack()[2:]:
            if self.program is None or str(Path(fr.filename).resolve()) == self.program:
                code = fr.code_context[0].strip() if fr.code_context else None
                return fr.lineno, code
        return None, None

    def _record(self, op, args, kwargs, **fields):
        line, code = self._caller()
        rec = {"step": len(self.steps) + 1, "op": op, "call": f"{op}({_short_repr(args, kwargs)})",
               "line": line, "code": code, "status": "ok", "error_type": None, "message": None,
               "hint": None, "checks": [], "geometry": None}
        rec.update(fields)
        self.steps.append(rec)
        return rec

    def _wrap(self, name, fn):
        trace = self

        def traced(self_wp, *args, **kwargs):
            if trace._depth:  # an operation calling other operations internally: don't log those
                return fn(self_wp, *args, **kwargs)
            trace._depth += 1
            try:
                before = _solid_of(self_wp)
                try:
                    out = fn(self_wp, *args, **kwargs)
                except Exception as e:
                    etype = type(e).__name__
                    rec = trace._record(name, args, kwargs, status="error", error_type=etype,
                                        message=str(e) or "(the kernel gave no message)",
                                        hint=exception_hint(name, etype))
                    raise IllegalOperation(rec) from e
                trace._check(name, args, kwargs, self_wp, out, before)
                return out
            finally:
                trace._depth -= 1

        traced.__wrapped__ = fn
        traced.__name__ = name
        return traced

    def _check(self, name, args, kwargs, wp_in, out, before):
        if not isinstance(out, cq.Workplane):
            return
        if name in SELECTORS and not out.objects:
            self._record(name, args, kwargs, status="warning", message="selector matched nothing",
                         hint=EMPTY_SELECTION_HINT, checks=["empty_selection"])
            return
        after = _result_solid(out)
        if after is None or _same(after, before):  # sketching / selecting: part unchanged
            if name in MODIFYING and before is not None:
                self._record(name, args, kwargs, status="warning", message="no_effect",
                             hint=NO_EFFECT_HINT, checks=["no_effect"])
            else:
                self._record(name, args, kwargs)
            return

        problems = brep_problems(after)
        geo = _geometry(after)
        if not after.Solids():
            rec = self._record(name, args, kwargs, status="error", error_type="NoSolid",
                               message="the operation removed all material (no solid left)",
                               hint="the cut/hole/intersection is larger than the part, or misses it "
                                    "entirely (intersect)", checks=["no_solid"], geometry=geo)
            raise IllegalOperation(rec)
        if problems:
            hints = [STATUS_HINTS[p] for p in problems if p in STATUS_HINTS]
            rec = self._record(name, args, kwargs, status="error", error_type="InvalidShape",
                               message="CAD kernel validity check failed: " + ", ".join(problems),
                               hint="; ".join(hints) or None, checks=problems, geometry=geo)
            raise IllegalOperation(rec)
        if geo["volume"] <= 1e-9 * after.BoundingBox().DiagonalLength ** 3:
            rec = self._record(name, args, kwargs, status="error", error_type="ZeroVolume",
                               message=f"the result has (near) zero volume ({geo['volume']:g})",
                               hint="the shape is flat or degenerate", checks=["zero_volume"],
                               geometry=geo)
            raise IllegalOperation(rec)

        warnings, hint = [], None
        if before is not None:
            gb = _geometry(before)
            geo["d_volume"] = round(geo["volume"] - gb["volume"], 6)
            if abs(geo["d_volume"]) <= 1e-6 * max(gb["volume"], 1e-12) and geo["n_faces"] == gb["n_faces"]:
                warnings.append("no_effect")
                hint = NO_EFFECT_HINT
            if geo["n_solids"] > gb["n_solids"] and geo["n_solids"] > 1:
                warnings.append("split_into_pieces")
                hint = (f"the part is now {geo['n_solids']} separate pieces; the feature probably "
                        f"cut it in two, or the new body doesn't touch the old one")
        # (a body built from scratch may be several pieces on purpose, e.g. hole cutters
        #  made with pushPoints; the final result is checked for that separately)
        self._record(name, args, kwargs, status="warning" if warnings else "ok", checks=warnings,
                     hint=hint, message=", ".join(warnings) or None, geometry=geo)

    def __enter__(self):
        for name, attr in vars(cq.Workplane).items():
            if name.startswith("_") or name in NOT_TRACED or not inspect.isfunction(attr):
                continue
            self._saved[name] = attr
            setattr(cq.Workplane, name, self._wrap(name, attr))
        return self

    def __exit__(self, *exc):
        for name, attr in self._saved.items():
            setattr(cq.Workplane, name, attr)
        self._saved.clear()
        return False

    def record_failure(self, exc, op="program"):
        """Log an error that didn't come from a traced operation (Python error in the
        program, missing `result`, final solid check), with the program line if known."""
        import traceback
        line = code = None
        for fr in traceback.extract_tb(exc.__traceback__):
            if self.program and str(Path(fr.filename).resolve()) == self.program:
                line, code = fr.lineno, fr.line
        if isinstance(exc, SyntaxError) and exc.lineno:
            line, code = exc.lineno, (exc.text or "").strip() or None
        rec = {"step": len(self.steps) + 1, "op": op, "call": op, "line": line, "code": code,
               "status": "error", "error_type": type(exc).__name__, "message": str(exc),
               "hint": getattr(exc, "hint", None), "checks": [], "geometry": None}
        self.steps.append(rec)
        return rec

    def record_result(self, shape):
        """Final check on what the program returned: warn if it is several pieces."""
        n = len(shape.Solids())
        if n > 1:
            self.steps.append({
                "step": len(self.steps) + 1, "op": "check_result", "call": "check_result",
                "line": None, "code": None, "status": "warning", "error_type": None,
                "message": "split_into_pieces", "checks": ["split_into_pieces"],
                "hint": f"the final part is {n} separate pieces that don't touch; "
                        f"a real part is usually one piece", "geometry": _geometry(shape)})

    def write_jsonl(self, path):
        import json
        Path(path).write_text("".join(json.dumps(s) + "\n" for s in self.steps))

    # -- summaries
    @property
    def errors(self):
        return [s for s in self.steps if s["status"] == "error"]

    @property
    def warnings(self):
        return [s for s in self.steps if s["status"] == "warning"]


def format_step(s):
    """One readable line per step, for printing (and for feeding back to a model)."""
    where = f"line {s['line']}" if s["line"] else "?"
    txt = f"[{s['status'].upper():7s}] step {s['step']:>2} ({where}) {s['call']}"
    if s["status"] != "ok":
        txt += f": {s['error_type'] + ': ' if s['error_type'] else ''}{s['message']}"
        if s["hint"]:
            txt += f"\n          hint: {s['hint']}"
    return txt
