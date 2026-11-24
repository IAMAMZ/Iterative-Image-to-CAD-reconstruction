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
        (ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py" / f"{name}.py").read_text()))
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "all",
                 "--rounds", "2", "--budget-seconds", "600", "--out", str(out)])
    part = out / "parts" / name
    assert (part / "questions.json").exists()
    assert (part / "internal" / "view_weights.json").exists()
    for arm in refine.ARMS:
        rows = [json.loads(l) for l in (part / arm / "log.jsonl").read_text().splitlines()]
        assert rows[0]["round"] == 0 and rows[0]["iou3d"] is not None
        final = json.loads((part / arm / "result.json").read_text())
        assert final["stop"] in ("rounds", "no_change", "all_questions_yes", "budget")
        assert "best_geo" in final and "best_oracle" in final
        # `final` points at the state the arm ended with, which has its program and mesh
        assert (part / arm / "final").resolve() == Path(final["final_dir"]).resolve()
        assert (part / arm / "final" / "program.py").exists()
        for r in rows[1:]:
            assert (part / arm / r["dir"]).is_dir()          # round_NN_<outcome>
            assert r["dir"].endswith(("kept", "rejected", "failed", "no-change", "stopped"))
            if r["status"] == "ok":       # every built edit carries the shadow geo decision
                assert isinstance(r["geo_decision"], bool) and r["verdict"] is not None
                assert r["prompt_tokens"] > 0
                assert r["dir"].endswith("kept" if r["accepted"] else "rejected")
                assert (part / arm / r["dir"] / "renders" / "top_front.png").exists()
                assert (part / arm / r["dir"] / "diff" / "summary.png").exists()
    s = summarize(out)
    assert set(s) == set(refine.ARMS)
    for f in ("parts.csv", "edits.csv", "summary.json"):
        assert (out / "results" / f).exists()
    # pages for humans, written by report.py
    for f in ("README.md", "results.md", "config.json", "log.txt",
              f"parts/{name}/compare.png", f"parts/{name}/scores.md",
              f"parts/{name}/progress.png", "results/figures/progress_by_part.png"):
        assert (out / f).exists(), f
    assert name in (out / "results.md").read_text()
    assert "finished" in (out / "README.md").read_text()


def test_failed_starting_program_is_skipped(f360_target, tmp_path):
    init = tmp_path / "init"
    init.mkdir()
    (init / f"{f360_target.name}.py").write_text("import cadquery as cq\nresult = cq.Workplane()\n")
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", "1", "--out", str(out)])
    part = out / "parts" / f360_target.name
    meta = json.loads((part / "init" / "internal" / "init.json").read_text())
    assert meta["ok"] is False and meta["error"]
    assert not (part / "geo").exists()
    assert (out / "README.md").exists()         # pages are written even when nothing ran


def test_default_run_folder_is_dated_and_named(f360_target, tmp_path, monkeypatch):
    init = tmp_path / "init"
    init.mkdir()
    (init / f"{f360_target.name}.py").write_text("import cadquery as cq\nresult = cq.Workplane()\n")
    monkeypatch.setattr(refine, "RUNS", tmp_path / "runs")
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", "1", "--name", "my test/run"])
    (run,) = (tmp_path / "runs").iterdir()
    assert run.name.endswith("_my-test-run") and run.name[:4].isdigit()


def test_all_yes_stop_rule():
    assert refine.stops_on_all_yes(refine.ARMS["vlm"], 0.5)           # CADCodeVerify: always
    assert not refine.stops_on_all_yes(refine.ARMS["hybrid"], 0.80)   # geometry disagrees
    assert refine.stops_on_all_yes(refine.ARMS["hybrid"], 0.99)       # both agree
