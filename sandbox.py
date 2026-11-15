"""Optional bubblewrap (bwrap) sandbox for building model-written CadQuery programs.

Linux only, opt-in (`refine.py --sandbox`, `cadrille_init.py convert --sandbox`); without the
flag builds run exactly as before, so macOS / Windows users are unaffected.

`vlm.check_code` is only a filter. Inside the sandbox a program that gets past it still
cannot reach the network or read or write anything it was not given:

  network            none (all namespaces unshared)
  home directory     hidden; only the repo's code, the Python environment and uv's Python
                     install are visible, read-only
  data               hidden (out/, data/, cadrille/ are empty); only the target's info.json
                     (normalisation for --like) is visible, read-only -- never gt.stl
  writable           only the candidate's output directory, and a fresh empty /tmp
  system             /usr, /etc, /sys read-only; GPU device nodes (EGL rendering)
  process            killed with the parent, own session, minimal environment

    from sandbox import wrap
    cmd = wrap(cmd, writable=[cand_dir], readonly=[target_dir / "info.json"])
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN = ("out", "data", "cadrille", "archive", ".git")   # repo folders the build never needs
KEEP_ENV = ("LANG", "LC_ALL", "PYOPENGL_PLATFORM", "__EGL_VENDOR_LIBRARY_FILENAMES",
            "CUDA_VISIBLE_DEVICES")


class SandboxUnavailable(RuntimeError):
    pass


def check():
    """Raise SandboxUnavailable with a readable reason if bwrap cannot be used here."""
    if not sys.platform.startswith("linux"):
        raise SandboxUnavailable(f"--sandbox needs Linux (bubblewrap); this is {sys.platform}")
    if shutil.which("bwrap") is None:
        raise SandboxUnavailable("--sandbox needs bubblewrap: install the `bubblewrap` package")


def _python_binds():
    """bwrap args exposing the interpreter: the venv and base install read-only, plus every
    symlink on the way to the real executable (uv links e.g. cpython-3.10-... ->
    cpython-3.10.22-...), recreated as symlinks."""
    dirs = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(),
            Path(sys.executable).resolve().parent.parent}
    links, hop = {}, Path(sys.executable).absolute()
    for _ in range(40):
        for anc in [hop, *hop.parents]:
            if anc.is_symlink() and not any(str(anc).startswith(str(d) + "/") for d in dirs) \
                    and not str(anc).startswith(str(ROOT) + "/"):
                links[str(anc)] = os.readlink(anc)
        if not hop.is_symlink():
            break
        hop = (hop.parent / os.readlink(hop)).absolute()
    a = []
    for d in sorted(dirs):
        a += ["--ro-bind", str(d), str(d)]
    for path, target in links.items():
        a += ["--symlink", target, path]
    return a


def wrap(cmd, writable=(), readonly=(), cwd=ROOT):
    """-> the bwrap command line that runs `cmd` confined as described above."""
    check()
    a = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
         "--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc", "--ro-bind", "/sys", "/sys",
         "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"]
    for d in ("/bin", "/sbin", "/lib", "/lib64", "/lib32"):    # merged-/usr symlinks or dirs
        p = Path(d)
        if p.is_symlink():
            a += ["--symlink", os.readlink(p), d]
        elif p.is_dir():
            a += ["--ro-bind", d, d]
    for dev in sorted(Path("/dev").glob("nvidia*")) + [Path("/dev/dri")]:
        if dev.exists():
            a += ["--dev-bind", str(dev), str(dev)]
    a += ["--ro-bind", str(ROOT), str(ROOT)]
    for h in HIDDEN:                                          # mask data inside the repo
        if (ROOT / h).is_dir():
            a += ["--tmpfs", str(ROOT / h)]
    a += _python_binds()
    for p in readonly:
        p = Path(p).resolve()
        a += ["--ro-bind", str(p), str(p)]
    for p in writable:
        p = Path(p).resolve()
        p.mkdir(parents=True, exist_ok=True)
        a += ["--bind", str(p), str(p)]
    env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1",
           **{k: os.environ[k] for k in KEEP_ENV if k in os.environ}}
    for k, v in env.items():
        a += ["--setenv", k, v]
    a += ["--chdir", str(Path(cwd).resolve()), "--"]
    return a + [str(c) for c in cmd]
