"""The optional bwrap sandbox (Linux only): builds still work, everything else is blocked."""
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

import refine
import sandbox
import vlm

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("bwrap") is None,
    reason="sandbox needs Linux + bubblewrap")

PROBE = r"""
import os, socket, sys
secret, repo, home, allowed = sys.argv[1:5]
allowed = set(allowed.split(","))
def blocked(fn):
    try:
        fn()
        return False
    except OSError:
        return True
print("secret", blocked(lambda: open(secret).read()))
print("net", blocked(lambda: socket.create_connection(("1.1.1.1", 80), timeout=3)))
print("repo_write", blocked(lambda: open(os.path.join(repo, "sandbox_probe.txt"), "w")))
print("data_hidden", all(not os.listdir(os.path.join(repo, d))
                         for d in ("out", "data", "cadrille") if os.path.isdir(os.path.join(repo, d))))
print("home_hidden", set(os.listdir(home)) <= allowed)
"""


def test_sandbox_blocks_files_network_and_writes(tmp_path):
    secret = tmp_path / "secret.txt"            # outside every bound path
    secret.write_text("x")
    home = Path.home()
    # the only entries of $HOME that may show up are the first steps towards bound paths
    allowed = {Path(p).resolve().relative_to(home).parts[0]
               for p in (ROOT, sys.prefix, sys.base_prefix, Path(sys.executable).resolve())
               if Path(p).resolve().is_relative_to(home)}
    cmd = sandbox.wrap([sys.executable, "-c", PROBE, secret, ROOT, home, ",".join(allowed)])
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    res = dict(l.split() for l in p.stdout.splitlines())
    assert res == {"secret": "True", "net": "True", "repo_write": "True",
                   "data_hidden": "True", "home_hidden": "True"}, p.stdout
    assert not (ROOT / "sandbox_probe.txt").exists()


def test_sandboxed_build_matches_plain_build(f360_target, tmp_path):
    src = (ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py" / f"{f360_target.name}.py").read_text()
    src += "\nresult = r\n"
    center = [0.0, 0.0, 0.0]
    assert refine.build(src, tmp_path / "plain", f360_target, center) is None
    assert refine.build(src, tmp_path / "boxed", f360_target, center, sandboxed=True) is None
    for f in ("front.png", "front_mask.png", "iso_fr_depth.png"):   # shading may differ by 1
        a, b = (np.asarray(Image.open(tmp_path / d / "renders" / f), dtype=int) for d in ("plain", "boxed"))
        assert a.shape == b.shape and np.abs(a - b).max() <= 1, f


def test_program_that_passes_check_code_cannot_write_outside(f360_target, tmp_path):
    """check_code is only a filter: CadQuery's own exporter can still write files anywhere.
    Without the sandbox the file appears; inside it, it does not."""
    def program(path):
        return ("import cadquery as cq\n"
                "result = cq.Workplane().box(10, 10, 10)\n"
                f"cq.exporters.export(result, {str(path)!r})\n")

    leak = tmp_path / "leak.step"                            # harmless place for the plain run
    assert vlm.check_code(program(leak)) is None             # the filter lets it through
    refine.build(program(leak), tmp_path / "plain", f360_target, [0, 0, 0])
    assert leak.exists()                                     # the gap is real

    escape = ROOT / "sandbox_escape_test.step"
    try:
        refine.build(program(escape), tmp_path / "boxed", f360_target, [0, 0, 0], sandboxed=True)
        assert not escape.exists()
    finally:
        escape.unlink(missing_ok=True)
