"""Parsing of agent replies."""
import vlm


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
    assert vlm.check_code("import cadquery as cq\nimport math\nresult = cq.Workplane().box(1, 1, 1)\n") is None
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


def test_repair_prompt_carries_the_error():
    assert "NameError: name 'w0'" in vlm.repair_prompt("NameError: name 'w0' is not defined")
