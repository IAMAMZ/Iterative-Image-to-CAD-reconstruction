"""View-confidence weights and the weighted geometric acceptance rule."""
import numpy as np
import pytest

from geo_check import geo_accept, geo_score, weighted_means
from rig import load_rig
from view_weights import consistency, to_weights


def _depths(target):
    d = np.load(target / "internal" / "depth.npz")
    return {k: d[k] for k in d.files}


@pytest.mark.parametrize("corrupt", ["shift", "depth_bias"])
def test_corrupted_view_gets_the_lowest_weight(f360_target, corrupt):
    d = _depths(f360_target)
    if corrupt == "shift":
        d["top_front"] = np.roll(d["top_front"], 30, axis=1)
    else:
        f = d["top_front"].astype(np.float32)
        f[f > 0] += 0.2
        d["top_front"] = f.astype(np.float16)
    w = to_weights(consistency(d, load_rig()))
    assert min(w, key=w.get) == "top_front"
    assert w["top_front"] < 0.9
    assert min(v for k, v in w.items() if k != "top_front") > 0.95   # the others stay trusted


def _report(ious, depth=0.01):
    return {"views": {v: {"iou": i, "depth_mae": depth} for v, i in ious.items()}}


def test_weighted_means():
    rep = _report({"a": 1.0, "b": 0.0})
    assert weighted_means(rep)[0] == pytest.approx(0.5)
    assert weighted_means(rep, {"a": 1.0, "b": 0.0})[0] == pytest.approx(1.0)


def test_drop_in_a_distrusted_view_does_not_veto():
    cur = _report({"a": 0.80, "b": 0.80, "c": 0.80})
    new = _report({"a": 0.90, "b": 0.90, "c": 0.70})    # c drops by 0.10
    keep_plain, _ = geo_accept(cur, new)
    keep_w, d = geo_accept(cur, new, {"a": 1.0, "b": 1.0, "c": 0.1})
    assert not keep_plain                                # trusted c vetoes
    assert keep_w and d["worst_view"] != "c"             # untrusted c is ignored


def test_drop_in_a_trusted_view_rejects():
    cur = _report({"a": 0.80, "b": 0.80, "c": 0.80})
    new = _report({"a": 0.95, "b": 0.95, "c": 0.70})
    keep, d = geo_accept(cur, new, {"a": 1.0, "b": 1.0, "c": 1.0})
    assert not keep and d["worst_view"] == "c"


def test_tiny_gain_is_inconclusive():
    cur = _report({"a": 0.8, "b": 0.8})
    keep, d = geo_accept(cur, _report({"a": 0.8001, "b": 0.8}))
    assert not keep and d["inconclusive"]
    assert geo_score(_report({"a": 0.9})) > geo_score(_report({"a": 0.8}))


def test_score_uses_the_union_depth_error():
    # same IoU and overlap MAE; the view whose outline misses more carries the larger
    # union depth error, and the score follows it
    a = {"views": {"v": {"iou": 0.8, "depth_mae": 0.01, "depth_err": 0.02}}}
    b = {"views": {"v": {"iou": 0.8, "depth_mae": 0.01, "depth_err": 0.05}}}
    assert geo_score(a) > geo_score(b)


def test_old_reports_fall_back_to_the_overlap_mae():
    assert weighted_means(_report({"a": 0.9}, depth=0.03))[1] == pytest.approx(0.03)
