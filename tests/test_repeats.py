"""Repeat-rate metric (summarize_runs.mark_repeats): proposals that redo a rejected attempt
from the same program state."""
from summarize_runs import edit_of, mark_repeats, normalize_program, repeat_stats

BASE = ("w0 = cq.Workplane('XY', origin=(0, 0, 14))\n"
        "r = w0.sketch().circle(100).circle(59, mode='s').finalize().extrude(-27)\n"
        "result = r\n")


def prog(depth=-27, hole=59, z=14):
    return BASE.replace("-27", str(depth)).replace("59", str(hole)).replace("14", str(z))


def test_reformatting_is_not_an_edit():
    messy = ('w0=cq.Workplane("XY",origin=(0,0,14.0))  # moved\n\n'
             "r=w0.sketch().circle(100).circle(59,mode='s').finalize().extrude(-27)\nresult=r")
    assert normalize_program(messy) == normalize_program(BASE)
    assert edit_of(normalize_program(BASE), normalize_program(messy))[0] == set()


def test_edits_of_different_features_do_not_overlap():
    b = normalize_program(BASE)
    depth, _ = edit_of(b, normalize_program(prog(depth=-27.5)))
    hole, _ = edit_of(b, normalize_program(prog(hole=61)))
    depth2, _ = edit_of(b, normalize_program(prog(depth=-28)))
    assert depth and not depth & hole
    assert depth == depth2              # same number changed, to another value


def _run(tmp_path, rounds):
    """rounds: [(program, accepted)] for one part/arm -> rows after mark_repeats."""
    part = tmp_path / "parts" / "p"
    (part / "init").mkdir(parents=True)
    (part / "init" / "program.py").write_text(BASE)
    rows = [{"part": "p", "arm": "geo", "round": 0, "status": "ok", "accepted": True}]
    for i, (src, acc) in enumerate(rounds, 1):
        d = f"round_{i:02d}_{'kept' if acc else 'rejected'}"
        (part / "geo" / d).mkdir(parents=True)
        (part / "geo" / d / "program.py").write_text(src)
        rows.append({"part": "p", "arm": "geo", "round": i, "status": "ok", "accepted": acc,
                     "dir": d})
    mark_repeats(tmp_path, rows)
    return rows


def test_repeat_after_rejection_is_flagged(tmp_path):
    rows = _run(tmp_path, [(prog(depth=-27.5), False),     # rejected
                           (prog(depth=-27.6), False),     # same spot, other value
                           (prog(hole=61), False)])        # a different feature
    r1, r2, r3 = rows[1:]
    assert not r1["repeat_eligible"]                       # nothing tried before
    assert r2["repeat_eligible"] and r2["repeat_spot"] and r2["repeat_of"] == 1
    assert not r2["repeat_exact"]
    assert r3["repeat_eligible"] and not r3["repeat_spot"] and r3["repeat_of"] is None
    s = repeat_stats(rows[1:])
    assert s["eligible"] == 2 and s["any"] == 0.5


def test_exact_repeat(tmp_path):
    rows = _run(tmp_path, [(prog(depth=-27.5), False), (prog(depth=-27.5), False)])
    assert rows[2]["repeat_exact"] and rows[2]["repeat_near"]


def test_kept_edit_starts_a_new_state(tmp_path):
    rows = _run(tmp_path, [(prog(depth=-27.5), True),      # kept: new state
                           (prog(depth=-27.5, z=13), False),
                           (prog(depth=-27.5, hole=61), False)])
    assert not rows[2]["repeat_eligible"]                  # first attempt from the new state
    assert rows[3]["repeat_eligible"] and not rows[3]["repeat_spot"]
