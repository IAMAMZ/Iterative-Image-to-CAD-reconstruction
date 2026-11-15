"""Geometric checker: IoU and depth numbers are right, and the overlay colours mean what they say."""
import json

import numpy as np
import pytest
from PIL import Image

from compare import BOTH, EXTRA, MISSING, compare, overlay_image, view_metrics
from generate_solid import generate
from rig import load_rig


# ------------------------------------------------------------ hand-made arrays
def square(y0, y1, x0, x1, depth=3.0, n=10):
    d = np.zeros((n, n), np.float32)
    d[y0:y1, x0:x1] = depth
    return d > 0, d


def test_iou_of_known_overlap():
    mt, dt = square(0, 4, 0, 4)          # 16 px
    mc, dc = square(0, 4, 2, 6)          # 16 px, 8 shared
    m = view_metrics(mt, dt, mc, dc)
    assert m["iou"] == pytest.approx(8 / 24)
    assert m["missing_px"] == 8 and m["extra_px"] == 8


def test_identical_views_are_perfect():
    mt, dt = square(2, 7, 1, 9)
    m = view_metrics(mt, dt, mt, dt.copy())
    assert m["iou"] == 1.0 and m["depth_mae"] == 0.0 and m["missing_px"] == m["extra_px"] == 0


def test_depth_error_only_counts_shared_pixels():
    mt, dt = square(0, 4, 0, 4, depth=3.0)
    mc, dc = square(0, 4, 0, 8, depth=3.1)   # extra pixels must not affect depth error
    m = view_metrics(mt, dt, mc, dc, mm_per_unit=10.0)
    assert m["depth_mae"] == pytest.approx(0.1, abs=1e-6)
    assert m["depth_mae_mm"] == pytest.approx(1.0, abs=1e-5)


def test_no_overlap_has_no_depth_error():
    mt, dt = square(0, 2, 0, 2)
    mc, dc = square(5, 7, 5, 7)
    m = view_metrics(mt, dt, mc, dc)
    assert m["iou"] == 0.0 and m["depth_mae"] is None


def test_overlay_colours():
    mt, _ = square(0, 4, 0, 4)
    mc, _ = square(0, 4, 2, 6)
    img = overlay_image(mt, mc)
    assert tuple(img[0, 0]) == MISSING    # target only -> red
    assert tuple(img[0, 5]) == EXTRA      # candidate only -> blue
    assert tuple(img[0, 3]) == BOTH


# ------------------------------------------------------------ real parts end to end
BOX = "import cadquery as cq\nresult = cq.Workplane().box({}, 20, 10)\n"


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Target box 40 mm long; candidates: the same box, and a box 20% longer."""
    tmp, rig = tmp_path_factory.mktemp("cmp"), load_rig()
    for name, length in (("target", 40), ("same", 40), ("longer", 48)):
        (tmp / f"{name}.py").write_text(BOX.format(length))
    generate(tmp / "target.py", tmp / "target", rig)
    norm = json.loads((tmp / "target" / "info.json").read_text())["normalization"]
    generate(tmp / "same.py", tmp / "same", rig, norm)
    generate(tmp / "longer.py", tmp / "longer", rig, norm)
    generate(tmp / "longer.py", tmp / "longer_own_frame", rig)  # the mistake: no shared frame
    return tmp


def test_same_part_scores_perfectly(runs):
    r = compare(runs / "target", runs / "same", runs / "out_same")
    assert r["mean_iou"] == 1.0 and r["mean_depth_mae"] == pytest.approx(0, abs=1e-6)


def test_longer_part_shows_extra_material_along_x(runs):
    r = compare(runs / "target", runs / "longer", runs / "out_longer")
    v = r["views"]
    assert v["front"]["iou"] < 0.95 and v["front"]["extra_px"] > 0
    assert v["front"]["missing_px"] == 0          # the longer box covers all of the target
    # looking along X (from the right) the end face is 4 mm closer. With a perspective camera
    # that makes it look a bit bigger: target fully covered, only extra material around it
    assert v["right"]["missing_px"] == 0 and v["right"]["extra_px"] > 0
    assert v["right"]["depth_mae_mm"] == pytest.approx(4.0, abs=0.1)  # end face 4 mm closer
    for f in ("summary.png", "report.json", "front_overlay.png", "front_depth_err.png"):
        assert (runs / "out_longer" / f).exists()
    # extra material is drawn blue in the overlay
    ov = np.asarray(Image.open(runs / "out_longer" / "front_overlay.png"))
    assert (ov == EXTRA).all(-1).any()


def test_without_shared_frame_a_bigger_part_looks_wrongly_close(runs, capsys):
    """Why --like exists: each part fitted to its own frame hides the size difference."""
    fair = compare(runs / "target", runs / "longer", runs / "o1")
    unfair = compare(runs / "target", runs / "longer_own_frame", runs / "o2")
    assert "different frames" in capsys.readouterr().err
    assert unfair["views"]["right"]["depth_mae"] < fair["views"]["right"]["depth_mae"]
