import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # import the root scripts

import pytest  # noqa: E402

PART = "101190_cfdcb477_0005"   # a small Fusion360 test part with a committed GT mesh


@pytest.fixture(scope="session")
def f360_target(tmp_path_factory):
    """One Fusion360 target dir (renders + depth + gt.stl), built once per test session."""
    from data.fusion360_targets import build_target
    from rig import load_rig
    root = tmp_path_factory.mktemp("targets")
    build_target(PART, root, load_rig())
    return root / PART
