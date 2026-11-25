"""`--patience K` (docs/ABLATION_PLAN.md F): tentative branches judged against the last
committed state, rolled back when they never beat it; the final state is always committed."""
import json
from pathlib import Path

import pytest

import geo_check
import refine
from cadrille_init import to_refine_program
from refine import Branch

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ state machine
def test_patience_zero_is_plain_keep_reject():
    b = Branch(0, "A")
    assert b.step(1, "x", False) == "rejected" and b.head == "A"
    assert b.step(2, "y", True) == "committed" and b.anchor == b.head == "y"


def test_patience_one_explores_then_rolls_back():
    b = Branch(1, "A")
    assert b.step(1, "x", False) == "tentative" and b.head == "x" and b.anchor == "A"
    assert b.on_branch and b.branch == [1]
    assert b.step(2, "y", False) == "rolled_back" and b.head == "A" and not b.on_branch
    assert b.rolled == [1, 2]
    assert b.step(3, "z", False) == "tentative"           # a fresh branch from the anchor


def test_branch_commits_when_it_beats_the_anchor():
    b = Branch(2, "A")
    b.step(1, "x", False)
    b.step(2, "y", False)
    assert b.steps == 2 and b.branch == [1, 2]
    assert b.step(3, "z", True) == "committed"
    assert b.anchor == b.head == "z" and b.anchor_round == 3 and b.steps == 0


def test_reverting_to_the_anchor_ends_the_branch():
    b = Branch(2, "A")
    b.step(1, "x", False)
    assert b.step(2, "A2", False, reverted=True) == "rolled_back" and b.head == "A"
    assert b.step(3, "A3", False, reverted=True) == "rejected"   # a no-op at the anchor


# ------------------------------------------------------------------ end to end (echo)
def _run(f360_target, tmp_path, monkeypatch, decisions, *flags):
    """Echo run of the geo arm with the check's keep decision scripted per round."""
    script = iter(decisions)
    real = geo_check.geo_accept

    def scripted(cur, new, *a, **k):
        _, d = real(cur, new, *a, **k)
        keep = next(script)
        reason = "kept" if keep else ("gain" if d["reason"] == "kept" else d["reason"])
        return keep, {**d, "keep": keep, "reason": reason}
    monkeypatch.setattr(refine, "geo_accept", scripted)
    init = tmp_path / "init"
    init.mkdir(parents=True)
    name = f360_target.name
    (init / f"{name}.py").write_text(to_refine_program(
        (ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py" / f"{name}.py").read_text()))
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", str(len(decisions)), "--out", str(out), *flags])
    part = out / "parts" / name / "geo"
    rows = [json.loads(l) for l in (part / "log.jsonl").read_text().splitlines()]
    conv = {r["round"]: json.loads((part / r["dir"] / "conversation.json").read_text())
            for r in rows[1:]}
    return rows, conv, part


def _program_in(prompt):
    return prompt.split("Current program:\n```python\n")[1].split("\n```")[0].strip()


def test_patience_run_commits_holds_and_rolls_back(f360_target, tmp_path, monkeypatch):
    rows, conv, part = _run(f360_target, tmp_path, monkeypatch,
                            [False, False, False, True, False],
                            "--patience", "1", "--feedback", "text")
    assert all(r["status"] == "ok" for r in rows[1:]), "echo should build every round"
    out = [r["patience_outcome"] for r in rows[1:]]
    assert out == ["tentative", "rolled_back", "tentative", "committed", "tentative"]
    assert [r["dir"].split("_", 2)[-1] for r in rows[1:]] == \
        ["tentative", "rolled-back", "tentative", "kept", "tentative"]
    assert [r["anchor_round"] for r in rows[1:]] == [0, 0, 0, 0, 4]
    assert [r["accepted"] for r in rows[1:]] == [False, False, False, True, False]
    # the agent edits the tentative head, not the anchor
    r1 = (part / rows[1]["dir"] / "program.py").read_text().strip()
    assert _program_in(conv[2]["prompt"]) == r1
    init = (part.parent / "init" / "program.py").read_text().strip()
    assert _program_in(conv[3]["prompt"]) == init               # rolled back to round 0
    assert "kept TENTATIVELY for 1 more round(s)" in conv[2]["prompt"]
    assert "TENTATIVELY for" not in conv[3]["prompt"]
    assert "ROLLED BACK to the program committed in round 0" in conv[3]["prompt"]
    assert "KEPT TENTATIVELY" in conv[2]["prompt"]
    # final = the last committed state (round 4), never the uncommitted round-5 branch
    res = json.loads((part / "result.json").read_text())
    assert Path(res["final_dir"]).name == rows[4]["dir"] and res["ended_on_branch"]
    assert (part / "final").resolve().name == rows[4]["dir"]


def test_branch_is_judged_against_the_anchor(f360_target, tmp_path, monkeypatch):
    seen = []
    real = geo_check.geo_accept

    def spy(cur, new, *a, **k):
        seen.append(cur)
        return False, {**real(cur, new, *a, **k)[1], "keep": False, "reason": "gain"}
    monkeypatch.setattr(refine, "geo_accept", spy)
    init = tmp_path / "init"
    init.mkdir()
    name = f360_target.name
    (init / f"{name}.py").write_text(to_refine_program(
        (ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py" / f"{name}.py").read_text()))
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", "2", "--patience", "2", "--out", str(tmp_path / "run")])
    assert len(seen) == 2 and seen[0] == seen[1]                # both vs round 0's report


@pytest.mark.parametrize("flags", [["--gate", "off"], ["--arm", "hybrid"], ["--patience", "-1"]])
def test_patience_rejects_bad_combinations(f360_target, tmp_path, flags):
    argv = [str(f360_target), "--backend", "echo", "--arm", "geo", "--patience", "1",
            "--out", str(tmp_path / "run"), *flags]
    with pytest.raises(SystemExit):
        refine.main(argv)
