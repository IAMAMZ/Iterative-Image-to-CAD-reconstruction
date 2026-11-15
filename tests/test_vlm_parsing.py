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
