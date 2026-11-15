"""The CadQuery reference entries match the installed CadQuery, and every example builds."""
from pathlib import Path

import cadquery as cq
import pytest

import cq_reference as R
import vlm

ROOT = Path(__file__).resolve().parents[1]
CADRILLE = ROOT / "cadrille" / "work_dirs" / "f360_rl" / "py"


@pytest.mark.parametrize("key", sorted(R.ENTRIES))
def test_entry_is_real_and_its_example_builds(key):
    owner, name = key.split(".")
    assert callable(getattr(R.OWNERS[owner], name))
    assert R.signature(key).startswith(key + "(")
    wp = eval(R.ENTRIES[key][1], {"cq": cq})
    solid = wp.val()
    assert isinstance(solid, cq.Shape) and solid.isValid() and solid.Volume() > 0, key


def test_alternatives_point_at_entries_and_wrong_owners_really_lack_the_method():
    for (owner, name), alts in R.WRONG_OWNER.items():
        assert not hasattr(R.OWNERS[owner], name), (owner, name)
        assert all(a in R.ENTRIES for a in alts)
    assert all(k in R.ENTRIES for alts in R.NEEDS.values() for k in alts)


def test_methods_used_follows_the_sketch_switch():
    src = ("import cadquery as cq\nw0=cq.Workplane('XY')\n"
           "r=w0.workplane(offset=2).moveTo(1,0).box(4,4,4).union("
           "w0.sketch().push([(0,1)]).circle(2).rect(3,3,mode='s').finalize().extrude(5))\n"
           "result = cq.Workplane(obj=r.val().scale(2))\n")
    used = R.methods_used(src)
    assert {"Workplane.moveTo", "Workplane.box", "Sketch.push", "Sketch.circle", "Sketch.rect",
            "Sketch.finalize", "Workplane.extrude", "Workplane.union"} <= set(used)
    assert "Sketch.box" not in used and "Workplane.circle" not in used


def test_program_reference_is_short_for_every_cadrille_program():
    for f in sorted(CADRILLE.glob("*.py"))[:60]:
        text = R.for_program(f.read_text())
        assert text.startswith("CadQuery reference") and len(text) / 4 < 1200, f.name


def test_error_reference():
    t = R.for_error("[ERROR  ] step  7 (line 21) program: AttributeError: "
                    "'Sketch' object has no attribute 'moveTo'")
    assert "Sketch.push(" in t and "Workplane.box(" not in t
    t = R.for_error("[ERROR  ] step  4 (line 9) cutBlind(-205): ValueError: No pending wires present")
    assert "Workplane.cutBlind(" in t and "Workplane.rect(" in t
    t = R.for_error("[ERROR  ] step  3 (line 4) fillet(2): ValueError: Fillets requires that edges be selected")
    assert "Workplane.edges(" in t
    assert "Workplane.box(length, width, height" in R.for_error(
        "[ERROR  ] step  1 (line 3) box(42, 5): TypeError: Workplane.box() missing 1 required "
        "positional argument: 'height'")
    assert R.for_error("something unrelated") == ""


def test_prompts_carry_the_reference():
    ref = R.for_program("import cadquery as cq\nresult = cq.Workplane('XY').box(1, 2, 3)\n")
    p = vlm.refine_prompt("import cadquery as cq\nresult = 1\n", [0, 0, 0], [1, 1, 1], reference=ref)
    assert "Workplane.box(" in p and p.index("CadQuery reference") < p.index("Current program:")
    assert "Workplane.box(" in vlm.repair_prompt("boom", reference=ref)
