"""Geometric checker: IoU and depth numbers are right, and the overlay colours mean what they say."""
import json

import numpy as np
import pytest
from PIL import Image

from compare import BOTH, DEPTH_CAP, EXTRA, MISSING, compare, overlay_image, view_metrics
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


def test_union_depth_error_counts_uncovered_pixels_at_the_cap():
    mt, dt = square(0, 4, 0, 4, depth=3.0)           # 16 px
    mc, dc = square(0, 4, 0, 8, depth=3.02)          # 32 px: 16 shared (error 0.02) + 16 extra
    m = view_metrics(mt, dt, mc, dc)
    assert m["depth_err"] == pytest.approx((16 * 0.02 + 16 * DEPTH_CAP) / 32, abs=1e-5)


def test_union_depth_error_caps_large_errors():
    mt, dt = square(0, 4, 0, 4, depth=3.0)
    mc, dc = square(0, 4, 0, 4, depth=4.0)           # full overlap, error 1.0 >> cap
    assert view_metrics(mt, dt, mc, dc)["depth_err"] == pytest.approx(DEPTH_CAP)


def test_union_depth_error_is_defined_without_overlap():
    mt, dt = square(0, 2, 0, 2)
    mc, dc = square(5, 7, 5, 7)
    assert view_metrics(mt, dt, mc, dc)["depth_err"] == pytest.approx(DEPTH_CAP)


def test_shrinking_the_overlap_cannot_hide_depth_error():
    # target: a 4x8 slab; good: same outline, small depth error everywhere;
    # gamed: only a sliver that matches exactly. The overlap-only MAE prefers the sliver.
    mt, dt = square(0, 4, 0, 8, depth=3.0)
    mg, dg = square(0, 4, 0, 8, depth=3.01)
    ms, ds = square(0, 4, 0, 1, depth=3.0)
    good, gamed = view_metrics(mt, dt, mg, dg), view_metrics(mt, dt, ms, ds)
    assert gamed["depth_mae"] < good["depth_mae"]
    assert good["depth_err"] < gamed["depth_err"]


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
    norm = json.loads((tmp / "target" / "internal" / "info.json").read_text())["normalization"]
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
    # the longer box contains the target, so every view shows only extra material
    for name in ("top_front", "top_back"):        # X runs across these images
        assert v[name]["iou"] < 0.95 and v[name]["extra_px"] > 0
    assert all(m["missing_px"] == 0 for m in v.values())
    # from the +X side the end face is 4 mm closer (seen at 45 deg, so more along the ray)
    assert v["top_right"]["extra_px"] > 0 and v["top_right"]["depth_mae_mm"] > 0.5
    for f in ("summary.png", "report.json", "top_front_overlay.png", "top_front_depth_err.png"):
        assert (runs / "out_longer" / f).exists()
    # extra material is drawn blue in the overlay
    ov = np.asarray(Image.open(runs / "out_longer" / "top_front_overlay.png"))
    assert (ov == EXTRA).all(-1).any()


def test_without_shared_frame_a_bigger_part_looks_wrongly_close(runs, capsys):
    """Why --like exists: each part fitted to its own frame hides the size difference."""
    fair = compare(runs / "target", runs / "longer", runs / "o1")
    unfair = compare(runs / "target", runs / "longer_own_frame", runs / "o2")
    assert "different frames" in capsys.readouterr().err
    assert unfair["mean_iou"] > fair["mean_iou"]   # shrunk to fit: silhouettes look closer
