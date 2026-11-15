"""What happens when a CadQuery program does something illegal?

Each case is a tiny part program. An illegal operation must be caught *at that
operation*: logged to ops_log.jsonl with its name, line, error and a hint, and the
run must fail without leaving a solid.step behind.
"""
import json
import math
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from generate_solid import generate
from op_checker import IllegalOperation, format_step
from rig import load_rig

ROOT = Path(__file__).resolve().parents[1]
HEADER = "import cadquery as cq\n"


def write_program(tmp_path, body):
    p = tmp_path / "part.py"
    p.write_text(HEADER + textwrap.dedent(body))
    return p


# name -> (program body, expected failing op, expected error type)
# Every illegal *operation* must be caught at that operation, with its name, error and line.
ILLEGAL = {
    # the CAD kernel refuses the operation
    "fillet_bigger_than_part": ("result = cq.Workplane().box(10, 10, 10).edges().fillet(20)",
                                "fillet", "StdFail_NotDone"),
    "zero_height_extrude":     ("result = cq.Workplane().rect(10, 10).extrude(0)",
                                "extrude", "Standard_ConstructionError"),
    "zero_size_box":           ("result = cq.Workplane().box(0, 10, 10)", "box", "Standard_DomainError"),
    "negative_size_box":       ("result = cq.Workplane().box(-1, 10, 10)", "box", "Standard_DomainError"),
    "selector_index_too_big":  ("result = cq.Workplane().box(10, 10, 10).faces('>X[7]').fillet(1)",
                                "faces", "IndexError"),
    # the kernel builds it, but its own validity check (BRepCheck) says it is illegal
    "self_intersecting_sketch": (
        "result = cq.Workplane().polyline([(0, 0), (10, 10), (10, 0), (0, 10)]).close().extrude(5)",
        "extrude", "InvalidShape"),
    # all material removed
    "cut_away_everything": (
        "result = cq.Workplane().box(10, 10, 10).cut(cq.Workplane().box(20, 20, 20))", "cut", "NoSolid"),
    "hole_bigger_than_part": (
        "result = cq.Workplane().box(10, 10, 10).faces('>Z').workplane().hole(50)", "hole", "NoSolid"),
    # the program itself is wrong (not a CAD operation)
    "python_error":            ("result = cq.Workplane().box(radius, 1, 1)", "program", "NameError"),
    "no_result_variable":      ("part = cq.Workplane().box(1, 1, 1)", "program", "ValueError"),
    "result_not_a_shape":      ("result = 42", "program", "TypeError"),
    "empty_workplane":         ("result = cq.Workplane()", "program", "ValueError"),
    # every op is legal, but the final result is not a solid
    "flat_2d_face_only":       ("result = cq.Workplane().rect(10, 10).extrude(1).faces('>Z').val()",
                                "check_result", "InvalidSolid"),
}

# legal programs that should log a warning (but still succeed)
WARNINGS = {
    "cut_that_misses": ("result = cq.Workplane().box(10, 10, 10)"
                        ".cut(cq.Workplane().center(50, 0).box(2, 2, 2))",
                        [("cut", ["no_effect"])]),
    "cut_in_two":      ("result = cq.Workplane().box(30, 10, 10).cut(cq.Workplane().box(2, 20, 20))",
                        [("cut", ["split_into_pieces"]), ("check_result", ["split_into_pieces"])]),
    "empty_selector":  ("result = cq.Workplane().box(10, 10, 10)\n_ = result.faces('%CONE')",
                        [("faces", ["empty_selection"])]),
    # several pieces built on purpose (hole cutters) are fine once they are used up
    "cutter_bodies_ok": ("cutters = cq.Workplane().pushPoints([(-3, 0), (3, 0)]).circle(1).extrude(10)\n"
                         "result = cq.Workplane().box(10, 5, 5).cut(cutters)", []),
}


def read_log(out):
    return [json.loads(l) for l in (out / "ops_log.jsonl").read_text().splitlines()]


@pytest.fixture(scope="module")
def rig():
    return load_rig()


@pytest.mark.parametrize("name", list(ILLEGAL))
def test_illegal_operation_is_caught_and_logged(name, tmp_path, rig):
    body, op, etype = ILLEGAL[name]
    program, out = write_program(tmp_path, body), tmp_path / "out"

    with pytest.raises(Exception) as err:
        generate(program, out, rig)

    if op not in ("program", "check_result"):
        assert isinstance(err.value, IllegalOperation)
    assert not (out / "solid.step").exists(), "a rejected shape must not be exported"

    log = read_log(out)                      # the log is written even though the run failed
    last = log[-1]
    print(f"{name}: {format_step(last)}")
    assert last["status"] == "error"
    assert (last["op"], last["error_type"]) == (op, etype)
    if op != "check_result" and name not in ("no_result_variable", "result_not_a_shape",
                                             "empty_workplane"):
        assert last["line"] == 2             # errors while running point at the line (1 = import)
    assert all(s["status"] == "ok" for s in log[:-1]), "steps before the illegal one were fine"
    if op not in ("program",) and etype != "IndexError":
        assert last["hint"], "illegal CAD operations come with a hint"


@pytest.mark.parametrize("name", list(WARNINGS))
def test_suspicious_operation_is_warned_about(name, tmp_path, rig):
    body, expected = WARNINGS[name]
    info = generate(write_program(tmp_path, body), tmp_path / "out", rig)
    warned = [s for s in read_log(tmp_path / "out") if s["status"] == "warning"]
    assert [(s["op"], s["checks"]) for s in warned] == expected
    assert all(s["hint"] for s in warned)
    assert len(info["ops"]["warnings"]) == len(expected)


def test_log_records_every_operation_of_a_chain(tmp_path, rig):
    body = "result = cq.Workplane().box(10, 10, 10).faces('>Z').workplane().hole(3)"
    generate(write_program(tmp_path, body), tmp_path / "out", rig)
    log = read_log(tmp_path / "out")
    assert [s["op"] for s in log] == ["box", "faces", "workplane", "hole"]
    assert all(s["status"] == "ok" for s in log)
    assert log[-1]["geometry"]["d_volume"] == pytest.approx(-math.pi * 1.5 ** 2 * 10, rel=1e-6)


def test_legal_shape_still_works(tmp_path, rig):
    """Sanity check: the checks don't reject a normal part."""
    program = write_program(tmp_path, "result = cq.Workplane().box(10, 20, 5).edges('|Z').fillet(1)")
    info = generate(program, tmp_path / "out", rig)
    assert info["valid"] and info["n_solids"] == 1
    assert info["volume"] == pytest.approx(10 * 20 * 5 - 4 * (1 - 3.14159265 / 4) * 5, rel=1e-4)
    for cam in info["views"]:
        assert (tmp_path / "out" / f"{cam}.png").exists()


def test_cli_exits_with_error_on_illegal_shape(tmp_path):
    """The command line reports failure with exit code 1 (what a loop would check)."""
    program = write_program(tmp_path, ILLEGAL["fillet_bigger_than_part"][0])
    r = subprocess.run([sys.executable, str(ROOT / "generate_solid.py"), str(program),
                        "--out", str(tmp_path / "out")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1
    assert "fillet(20)" in r.stderr and "hint:" in r.stderr
