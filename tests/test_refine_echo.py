"""The whole refinement loop end to end with the fake `echo` agent (no model needed)."""
import json
from pathlib import Path

import refine
from cadrille_init import to_refine_program
from summarize_runs import summarize

ROOT = Path(__file__).resolve().parents[1]


def test_refine_all_arms_with_echo(f360_target, tmp_path):
    init = tmp_path / "init"
    init.mkdir()
    name = f360_target.name
    (init / f"{name}.py").write_text(to_refine_program(
        (ROOT / "cadrille" / "work_dirs" / "f360_rl" / "py" / f"{name}.py").read_text()))
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "all",
                 "--rounds", "2", "--budget-seconds", "600", "--out", str(out)])
    part = out / name
    assert (part / "questions.json").exists() and (part / "view_weights.json").exists()
    for arm in refine.ARMS:
        rows = [json.loads(l) for l in (part / arm / "results.jsonl").read_text().splitlines()]
        assert rows[0]["round"] == 0 and rows[0]["iou3d"] is not None
        final = json.loads((part / arm / "final.json").read_text())
        assert final["stop"] in ("rounds", "no_change", "all_questions_yes", "budget")
        assert "best_geo" in final and "best_oracle" in final
        for r in rows[1:]:
            if r["status"] == "ok":       # every built edit carries the shadow geo decision
                assert isinstance(r["geo_decision"], bool) and r["verdict"] is not None
                assert r["prompt_tokens"] > 0
    s = summarize(out)
    assert set(s) == set(refine.ARMS)
    assert (out / "per_part.csv").exists() and (out / "edits.csv").exists()


def test_failed_starting_program_is_skipped(f360_target, tmp_path):
    init = tmp_path / "init"
    init.mkdir()
    (init / f"{f360_target.name}.py").write_text("import cadquery as cq\nresult = cq.Workplane()\n")
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", "1", "--out", str(out)])
    meta = json.loads((out / f360_target.name / "init" / "init.json").read_text())
    assert meta["ok"] is False and meta["error"]
    assert not (out / f360_target.name / "geo").exists()
