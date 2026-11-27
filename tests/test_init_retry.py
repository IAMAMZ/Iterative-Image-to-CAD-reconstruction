"""A starting program that fails to build is retried once before its part is skipped."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import refine  # noqa: E402


def _run(tmp_path, monkeypatch, outcomes):
    calls = []

    def fake_build(src, d, target, center, sandbox):
        calls.append(src)
        return outcomes[len(calls) - 1]

    monkeypatch.setattr(refine, "build", fake_build)
    monkeypatch.setattr(refine.time, "sleep", lambda s: None)
    init = tmp_path / "init"
    init.mkdir()
    (init / "part.py").write_text("result = None\n")
    args = argparse.Namespace(init=init, sandbox=False)
    part_out = tmp_path / "out"
    ok = refine.prepare_init(args, None, tmp_path / "part", part_out, None, None, None, None)
    meta = json.loads((part_out / "init" / layout.INTERNAL / "init.json").read_text())
    return ok, calls, meta


def test_transient_failure_is_retried(tmp_path, monkeypatch):
    ok, calls, meta = _run(tmp_path, monkeypatch, ["IndexError: list index out of range", None])
    assert ok and meta["ok"] and len(calls) == 2


def test_persistent_failure_skips_the_part(tmp_path, monkeypatch):
    ok, calls, meta = _run(tmp_path, monkeypatch, ["boom", "boom again"])
    assert not ok and not meta["ok"] and meta["error"] == "boom again" and len(calls) == 2
