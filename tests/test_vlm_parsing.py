"""Parsing of agent replies and the display formatting of cadrille programs."""
import ast

import vlm

CADRILLE_LIKE = (
    "import cadquery as cq\n"
    "w0=cq.Workplane('YZ',origin=(51,0,0))\n"
    "r=w0.sketch().segment((-84,-24),(75,-24)).segment((75,12)).segment((-84,12)).close()"
    ".assemble().push([(-88,13)]).circle(6.5,mode='s').finalize().extrude(-102)"
    ".union(w0.workplane(offset=5/2).moveTo(67,19.5).box(10.5,3.5,1))\n"
    "result = r\n")


def test_format_program_keeps_the_program():
    f = vlm.format_program(CADRILLE_LIKE)
    assert f != CADRILLE_LIKE and max(len(l) for l in f.splitlines()) < 120
    assert ast.dump(ast.parse(f)) == ast.dump(ast.parse(CADRILLE_LIKE))


def test_format_program_leaves_bad_code_alone():
    assert vlm.format_program("x = (\n") == "x = (\n"


def test_parse_change():
    assert vlm.parse_change("CHANGE: Structural - add the boss\n```python\nx\n```") == \
        ("structural", "add the boss")
    assert vlm.parse_change("CHANGE: **dimensional** — thicker plate") == ("dimensional", "thicker plate")
    assert vlm.parse_change("NO_CHANGE") == ("no_change", None)
    assert vlm.parse_change("here is code\n```python\nx\n```") == (None, None)


def test_questions_and_answers():
    qs = vlm.parse_questions("1. Is it a plate?\n2) **Does it have 4 holes?**\n3. Is it a plate?\nnot a q")
    assert qs == ["Is it a plate?", "Does it have 4 holes?"]
    ans = vlm.parse_answers("1. **Is it a plate?**\n- **Answer:** Yes\n- **Reasoning:** x\n"
                            "2. **Q?**\n- **Answer:** no\n", 3)
    assert ans == ["yes", "no", "unclear"]
    assert vlm.qa_text(qs, ["yes", "no"], only_failed=True) == "2. Does it have 4 holes? -> No"


def test_judgement_and_code():
    assert vlm.parse_judgement("A looks closer\nKEEP B") == "B"
    assert vlm.check_code(CADRILLE_LIKE) is None
    assert "result" in vlm.check_code("import cadquery as cq\nr = 1\n")
    assert vlm.check_code("import os\nresult = 1\n") is not None


def test_kernel_report_lists_warnings():
    txt = vlm.kernel_report({"n_solids": 2, "n_faces": 10, "volume": 5.0,
                             "ops": {"warnings": ["[WARNING] step 3 union: split_into_pieces"]}})
    assert "2 solid piece" in txt and "split_into_pieces" in txt


def test_echo_backend_edits_the_program():
    text, st = vlm.chat([{"role": "user", "content": "fix\n```python\nimport cadquery as cq\n"
                          "result = cq.Workplane().box(10, 20, 30)\n```"}], backend="echo")
    kind, _ = vlm.parse_change(text)
    assert kind in ("dimensional", "no_change") and st["output_tokens"] > 0


BASE = ("import cadquery as cq\n"
        "w0=cq.Workplane('XY',origin=(0,0,100))\n"
        "w1=w0.workplane(offset=5)\n"
        "r=w0.box(10,10,10)\n"
        "result = r\n")


def test_restore_dropped_workplane_definition():
    reply = "import cadquery as cq\n\nresult = w0.box(10, 20, 30)\n"
    src, names = vlm.restore_definitions(reply, BASE)
    assert names == ["w0"]
    assert src.splitlines()[0] == "import cadquery as cq" and "w0=cq.Workplane" in src
    assert vlm.undefined_names(src) == set()


def test_restore_pulls_in_dependencies_in_order():
    src, names = vlm.restore_definitions("import cadquery as cq\nresult = w1.box(1, 1, 1)\n", BASE)
    assert names == ["w0", "w1"] and src.index("w0=") < src.index("w1=")


def test_restore_leaves_complete_or_unparsable_programs_alone():
    ok = "import cadquery as cq\nw0 = cq.Workplane('XZ')\nresult = w0.box(1, 1, 1)\n"
    assert vlm.restore_definitions(ok, BASE) == (ok, [])        # its own w0 wins
    assert vlm.restore_definitions("x = (\n", BASE) == ("x = (\n", [])
    assert vlm.restore_definitions("result = w0.box(1,1,1)\n", None)[1] == []
    assert vlm.undefined_names("import math\nresult = [math.pi * i for i in range(3)]\n") == set()


def test_repair_prompt_quotes_the_missing_definition():
    txt = vlm.repair_prompt("[ERROR] step 1: NameError: name 'w0' is not defined", BASE, repeated=True)
    assert "w0=cq.Workplane('XY',origin=(0,0,100))" in txt and "identical" in txt
    assert "never defined" in vlm.repair_prompt("NameError: name 'zz' is not defined", BASE)
    assert "identical" not in vlm.repair_prompt("boom", BASE)


def test_repair_prompt_explains_sketch_api_mixups():
    t = vlm.repair_prompt("AttributeError: 'Sketch' object has no attribute 'moveTo'")
    assert ".push([(x, y)])" in t
    assert "finalize()" in vlm.repair_prompt("AttributeError: 'Sketch' object has no attribute 'extrude'")
    assert "val().scale" in vlm.repair_prompt("AttributeError: 'Workplane' object has no attribute 'scale'")
    assert "How to fix" not in vlm.repair_prompt("ValueError: something else")
