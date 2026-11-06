"""What happens when a CadQuery program makes an illegal shape?

Each case is a tiny part program. A good program must produce a checked solid;
a bad one must fail with an error and must NOT leave a solid.step behind.
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from generate_solid import InvalidSolid, generate
from rig import load_rig

ROOT = Path(__file__).resolve().parents[1]
HEADER = "import cadquery as cq\n"


def write_program(tmp_path, body):
    p = tmp_path / "part.py"
    p.write_text(HEADER + textwrap.dedent(body))
    return p


# name -> (program body, what should go wrong)
#   "kernel"  : CadQuery/OpenCascade refuses to build it (script crashes)
#   "invalid" : it builds, but our check rejects the result (InvalidSolid)
#   "program" : the file itself is wrong (no/odd `result`)
ILLEGAL = {
    "fillet_bigger_than_part": ("result = cq.Workplane().box(10, 10, 10).edges().fillet(20)", "kernel"),
    "zero_height_extrude":     ("result = cq.Workplane().rect(10, 10).extrude(0)", "kernel"),
    "zero_size_box":           ("result = cq.Workplane().box(0, 10, 10)", "kernel"),
    "negative_size_box":       ("result = cq.Workplane().box(-1, 10, 10)", "kernel"),
    "self_intersecting_sketch": (
        "result = cq.Workplane().polyline([(0, 0), (10, 10), (10, 0), (0, 10)]).close().extrude(5)",
        "invalid"),
    "cut_away_everything": (
        "result = cq.Workplane().box(10, 10, 10).cut(cq.Workplane().box(20, 20, 20))", "invalid"),
    "hole_bigger_than_part": (
        "result = cq.Workplane().box(10, 10, 10).faces('>Z').workplane().hole(50)", "invalid"),
    "flat_2d_face_only":       ("result = cq.Workplane().rect(10, 10).extrude(1).faces('>Z').val()", "invalid"),
    "no_result_variable":      ("part = cq.Workplane().box(1, 1, 1)", "program"),
    "result_not_a_shape":      ("result = 42", "program"),
    "empty_workplane":         ("result = cq.Workplane()", "program"),
}


@pytest.fixture(scope="module")
def rig():
    return load_rig()


@pytest.mark.parametrize("name", list(ILLEGAL))
def test_illegal_shape_is_rejected(name, tmp_path, rig):
    body, kind = ILLEGAL[name]
    program, out = write_program(tmp_path, body), tmp_path / "out"

    with pytest.raises(Exception) as err:
        generate(program, out, rig)

    if kind == "invalid":
        assert isinstance(err.value, InvalidSolid)
    elif kind == "program":
        assert isinstance(err.value, (ValueError, TypeError))
        assert not isinstance(err.value, InvalidSolid)
    else:  # kernel errors come from OpenCascade, not from our checks
        assert not isinstance(err.value, InvalidSolid)
    print(f"{name}: {type(err.value).__name__}: {err.value}")
    assert not (out / "solid.step").exists(), "a rejected shape must not be exported"


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
    program = write_program(tmp_path, ILLEGAL["self_intersecting_sketch"][0])
    r = subprocess.run([sys.executable, str(ROOT / "generate_solid.py"), str(program),
                        "--out", str(tmp_path / "out")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1
    assert "InvalidSolid" in r.stderr
