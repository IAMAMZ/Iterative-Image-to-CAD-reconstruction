"""Edit feedback (docs/FEEDBACK_PLAN.md): attempt log, round history, repeat guard,
edit-effect image, and that none of it leaks the hidden ground truth."""
import json
import re
from pathlib import Path

import numpy as np
import pytest

import refine
import vlm
from cadrille_init import to_refine_program
from compare import BOTH, BROKE, FIXED, STILL_WRONG, edit_effect_image
from geo_check import edit_delta, geo_accept
from summarize_runs import normalize_program

ROOT = Path(__file__).resolve().parents[1]


def _rep(ious, missing=10, extra=5, depth=0.01):
    return {"mm_per_unit": 1.0, "views": {
        v: {"iou": i, "missing_px": missing, "extra_px": extra, "depth_mae": depth,
            "depth_err": depth} for v, i in ious.items()}}


# ------------------------------------------------------------------ checker side
def test_reject_reasons():
    cur = _rep({"a": 0.80, "b": 0.80})
    assert geo_accept(cur, _rep({"a": 0.90, "b": 0.90}))[1]["reason"] == "kept"
    assert geo_accept(cur, _rep({"a": 0.8001, "b": 0.80}))[1]["reason"] == "inconclusive"
    assert geo_accept(cur, _rep({"a": 0.70, "b": 0.80}))[1]["reason"] == "gain"
    assert geo_accept(cur, _rep({"a": 0.99, "b": 0.74}))[1]["reason"] == "view_drop"


def test_edit_delta_names_the_worst_view_and_what_went_wrong():
    cur = _rep({"a": 0.9, "b": 0.9}, extra=5)
    new = {"mm_per_unit": 1.0, "views": {
        "a": {"iou": 0.95, "missing_px": 5, "extra_px": 5, "depth_mae": 0.01, "depth_err": 0.01},
        "b": {"iou": 0.80, "missing_px": 10, "extra_px": 900, "depth_mae": 0.01, "depth_err": 0.01}}}
    d = edit_delta(cur, new)
    assert d["worst_view"] == "b" and d["mostly"] == "extra" and d["best_view"] == "a"
    assert d["views"]["b"]["iou"] == (0.9, 0.80)


def test_edit_effect_image_colours():
    t = np.zeros((4, 4), bool)
    t[:, :2] = True                           # target: left half
    cur = t.copy()
    cur[0, 0] = False                         # wrong before (missing), fixed by the edit
    cur[0, 3] = True                          # wrong before (extra), still wrong after
    new = t.copy()
    new[0, 3] = True
    new[3, 1] = False                         # right before, broken by the edit
    img, n = edit_effect_image(t, cur, new)
    assert tuple(img[0, 0]) == FIXED and tuple(img[3, 1]) == BROKE
    assert tuple(img[0, 3]) == STILL_WRONG and tuple(img[1, 1]) == BOTH
    assert n == {"fixed": 1, "broke": 1}


# ------------------------------------------------------------------ prompt side
def _entry(rnd, outcome="rejected", reason="gain"):
    return {"round": rnd, "outcome": outcome, "reason": reason, "tag": "dimensional",
            "change": f"change {rnd}", "diff": ["- a = 1", "+ a = 2"], "gain": -0.01,
            "worst_view": "top_front", "worst_view_drop": -0.02, "min_gain": 1e-3,
            "max_view_drop": 0.05, "delta": edit_delta(_rep({"top_front": 0.9}),
                                                       _rep({"top_front": 0.8}, extra=99))}


def test_feedback_block_lists_attempts_and_history():
    text = vlm.feedback_block([_entry(1), _entry(2)], ["round 1: rejected", "round 2: rejected"],
                              effect_image=6)
    assert "Attempt in round 1" in text and "Attempt in round 2" in text
    assert "geometric score fell by 0.0100" in text and "- a = 1" in text
    assert "Image 6 shows what the attempt in round 2 changed" in text
    assert "do not repeat a rejected change" in text and "Round history" in text
    assert "```" not in text                  # never a code fence: the program block stays last
    assert vlm.feedback_block([], []) is None


def test_mask_signal_hides_depth_and_depth_signal_hides_outline():
    m = vlm.feedback_block([_entry(1)], [], signal="mask")
    d = vlm.feedback_block([_entry(1)], [], signal="depth")
    assert "IoU" in m and "depth MAE" not in m
    assert "depth MAE" in d and "missing px" not in d


# ------------------------------------------------------------------ repeat guard
def test_repeat_guard_blocks_without_building(monkeypatch, tmp_path):
    src = "import cadquery as cq\nresult = cq.Workplane().box(10, 10, 10)\n"
    reply = f"CHANGE: dimensional - same again\n```python\n{src}```"
    monkeypatch.setattr(vlm, "chat", lambda *a, **k: (reply, {"seconds": 0.0}))
    monkeypatch.setattr(refine, "build", lambda *a, **k: pytest.fail("a repeat was built"))
    agent = refine.Agent("echo", False, repairs=1, backend="echo")
    status, n, tr, _ = agent.write_program(
        "edit", [], tmp_path / "c", tmp_path, [0, 0, 0],
        tried=[(3, normalize_program(src.replace("10, 10", "10.0,10")))])   # same once normalised
    assert status == "repeat_blocked" and n == 2
    assert all(t["repeat_of"] == 3 for t in tr)


# ------------------------------------------------------------------ end to end (echo)
def _run(f360_target, tmp_path, *flags, rounds=5):
    init = tmp_path / "init"
    init.mkdir(parents=True)
    name = f360_target.name
    (init / f"{name}.py").write_text(to_refine_program(
        (ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py" / f"{name}.py").read_text()))
    out = tmp_path / "run"
    refine.main([str(f360_target), "--init", str(init), "--backend", "echo", "--arm", "geo",
                 "--rounds", str(rounds), "--out", str(out), *flags])
    part = out / "parts" / name / "geo"
    rows = [json.loads(l) for l in (part / "log.jsonl").read_text().splitlines()]
    prompts = {r["round"]: json.loads((part / r["dir"] / "conversation.json").read_text())["prompt"]
               for r in rows[1:] if r.get("dir") and r["status"] != "stopped"}
    return rows, prompts, part


def test_attempt_log_follows_rejections_and_resets_on_keep(f360_target, tmp_path):
    rows, prompts, part = _run(f360_target, tmp_path, "--feedback", "image")
    since_keep = 0
    for prev, r in zip(rows[1:], rows[2:]):
        if prev["status"] == "no_change":
            break
        p = prompts[r["round"]]
        since_keep = 0 if prev.get("accepted") else since_keep + 1
        assert r["feedback_attempts"] == min(since_keep, refine.FB_ATTEMPTS)
        assert (f"Attempt in round {prev['round']}" in p) == (not prev.get("accepted"))
        assert f"round {prev['round']}:" in p                    # round history
        if prev["status"] == "ok" and not prev.get("accepted"):  # effect image of a rejection
            assert (part / prev["dir"] / "diff" / "effect.json").exists()


def test_feedback_never_leaks_the_ground_truth(f360_target, tmp_path):
    _, prompts, _ = _run(f360_target, tmp_path, "--feedback", "image")
    for p in prompts.values():
        low = p.lower()
        for word in ("iou3d", "3d iou", "chamfer", "hausdorff", "beneficial", "harmful",
                     "verdict", "gt.stl", "ground truth"):
            assert word not in low, word


def test_feedback_none_sends_the_old_prompt(f360_target, tmp_path):
    rows, prompts, part = _run(f360_target, tmp_path, "--feedback", "none", rounds=3)
    for p in prompts.values():
        assert "Previous attempts" not in p and "Round history" not in p
    assert not list(part.glob("*/diff/effect.json"))
    assert all("feedback_attempts" not in r for r in rows)


def test_gate_off_feedback_reports_the_last_edit(f360_target, tmp_path):
    rows, prompts, _ = _run(f360_target, tmp_path, "--feedback", "text", "--gate", "off",
                            rounds=3)
    for prev, r in zip(rows[1:], rows[2:]):
        if prev["status"] == "ok" and r["round"] in prompts:
            assert "every edit is kept in this run" in prompts[r["round"]]
            assert re.search(r"geometric check would have (kept|rejected) it", prompts[r["round"]])
