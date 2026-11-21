"""Stage 2 corruptions (corrupt.py) and the checker study's edit generator (checker_eval.py)."""
import json
import random

import numpy as np
import pytest

import layout
from corrupt import KINDS, LEVELS, corrupt_depths, corrupt_target, corrupt_view, rng_for


def _square(h=128, depth=3.0):
    d = np.zeros((h, h), np.float32)
    d[32:96, 32:96] = depth
    return d


@pytest.mark.parametrize("kind", KINDS)
def test_level_0_is_the_clean_view(kind):
    d = _square()
    assert np.array_equal(corrupt_view(d, kind, 0, np.random.default_rng(0)), d)


@pytest.mark.parametrize("kind", KINDS)
def test_every_level_changes_something(kind):
    d = _square()
    for lv in LEVELS[kind]:
        assert not np.array_equal(corrupt_view(d, kind, lv, np.random.default_rng(0)), d)


def test_erode_shrinks_and_dilate_grows_by_r_pixels():
    d = _square()
    m = d > 0
    for lv, p in LEVELS["erode"].items():
        e = corrupt_view(d, "erode", lv, None) > 0
        assert (e <= m).all() and e.sum() == (64 - 2 * p["r"]) ** 2
    for lv in LEVELS["dilate"]:
        g = corrupt_view(d, "dilate", lv, None)
        assert ((g > 0) >= m).all()
        assert np.allclose(g[g > 0], 3.0)          # gained pixels take the nearest depth


@pytest.mark.parametrize("kind", ["depth_noise", "depth_scale"])
def test_depth_corruptions_keep_the_silhouette(kind):
    d = _square()
    for lv in LEVELS[kind]:
        n = corrupt_view(d, kind, lv, np.random.default_rng(1))
        assert np.array_equal(n > 0, d > 0)
        assert not np.allclose(n, d)


def test_severity_grows_with_level_and_reuses_the_same_draws():
    d = {"a": _square(), "b": _square()}
    for kind in ("holes", "blobs", "jitter", "erode", "dilate", "bad_view"):
        lost = []
        for lv in (1, 2, 3):
            n, hit = corrupt_depths(d, "p", kind, lv)
            lost.append(sum(((n[v] > 0) ^ (d[v] > 0)).sum() for v in d))
        assert lost[0] < lost[1] < lost[2], kind
    # holes: level 1's holes are still there at level 2
    h1 = corrupt_depths(d, "p", "holes", 1)[0]["a"] > 0
    h2 = corrupt_depths(d, "p", "holes", 2)[0]["a"] > 0
    assert (h2 <= h1).all()


def test_bad_view_hits_one_view_the_same_one_at_every_level():
    d = {v: _square() for v in "abcdefgh"}
    hits = [corrupt_depths(d, "part", "bad_view", lv)[1] for lv in (1, 2, 3)]
    assert all(len(h) == 1 for h in hits) and hits[0] == hits[1] == hits[2]
    n, hit = corrupt_depths(d, "part", "bad_view", 3)
    assert all(np.array_equal(n[v], d[v]) for v in d if v not in hit)


def test_seeded():
    d = _square()
    a = corrupt_view(d, "jitter", 2, rng_for("p", "jitter", 0, "front"))
    b = corrupt_view(d, "jitter", 2, rng_for("p", "jitter", 0, "front"))
    c = corrupt_view(d, "jitter", 2, rng_for("p", "jitter", 1, "front"))
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_corrupt_target_changes_only_the_measurements(f360_target, tmp_path):
    from view_weights import view_weights
    view_weights(f360_target)                       # make sure a clean cache exists to drop
    dst = tmp_path / "bad_view_L3" / f360_target.name
    rec = corrupt_target(f360_target, dst, "bad_view", 3)
    hit = rec["views"][0]
    assert layout.is_rendered(dst)
    assert not layout.internal(dst, "view_weights.json").exists()
    clean, noisy = np.load(layout.depth(f360_target)), np.load(layout.depth(dst))
    assert not np.array_equal(clean[hit], noisy[hit])
    assert all(np.array_equal(clean[v], noisy[v]) for v in clean.files if v != hit)
    # the shaded picture the agent sees and the ground truth are untouched
    assert layout.render(dst, hit).read_bytes() == layout.render(f360_target, hit).read_bytes()
    assert (dst / "gt.stl").read_bytes() == (f360_target / "gt.stl").read_bytes()
    a = json.loads(layout.info(f360_target).read_text())
    b = json.loads(layout.info(dst).read_text())
    assert a["normalization"] == b["normalization"]
    assert b["corruption"]["kind"] == "bad_view" and b["corruption"]["error"][hit]["mask_iou"] < 1
    # and the view weights notice the bad view
    w = view_weights(dst)
    assert min(w, key=w.get) == hit


def test_perturb_changes_exactly_one_number():
    from checker_eval import NUM, perturb
    src = ("import cadquery as cq\nw0=cq.Workplane('XY',origin=(0,0,5))\n"
           "r=w0.box(10,20,3.5).faces('>Z').hole(2)\nresult = r\n")
    rng = random.Random(0)
    for _ in range(20):
        new, desc = perturb(src, rng)
        a, b = NUM.findall(src), NUM.findall(new)
        assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1, desc
        assert "w0" in new and "Workplane('XY'" in new
