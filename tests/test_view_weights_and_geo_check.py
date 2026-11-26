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


# ------------------------------------------------ --geo-signal ablation (mask / depth / both)
def _rep(iou, depth_err):
    return {"views": {"a": {"iou": iou, "depth_mae": depth_err, "depth_err": depth_err,
                            "missing_px": 10, "extra_px": 5}}}


def test_signal_picks_what_the_score_sees():
    better_outline = _rep(0.95, 0.05)
    better_depth = _rep(0.85, 0.01)
    assert geo_score(better_outline, signal="mask") > geo_score(better_depth, signal="mask")
    assert geo_score(better_depth, signal="depth") > geo_score(better_outline, signal="depth")
    assert geo_score(better_depth) == pytest.approx(0.85 - 0.01)


def test_depth_signal_has_no_iou_guard():
    cur = {"views": {"a": _rep(0.9, 0.05)["views"]["a"], "b": _rep(0.9, 0.05)["views"]["a"]}}
    new = {"views": {"a": _rep(0.9, 0.01)["views"]["a"], "b": _rep(0.80, 0.04)["views"]["a"]}}
    keep_both, _ = geo_accept(cur, new)                     # b's IoU drops by 0.10: vetoed
    keep_depth, d = geo_accept(cur, new, signal="depth")    # depth error fell in both views
    keep_mask, _ = geo_accept(cur, new, signal="mask")      # outline only got worse
    assert not keep_both and keep_depth and not keep_mask
    assert d["signal"] == "depth" and d["worst_view"] == "b"


def test_residual_table_shows_only_the_active_signal():
    from geo_check import residual_table
    rep = _rep(0.9, 0.02)
    assert "IoU" in residual_table(rep) and "depth" in residual_table(rep)
    assert "IoU" in residual_table(rep, signal="mask") and "depth" not in residual_table(rep, signal="mask")
    t = residual_table(rep, signal="depth")
    assert "depth" in t and "IoU" not in t and "missing" not in t


def test_restrict_keeps_only_the_chosen_views():
    from geo_check import restrict
    rep = _report({"a": 0.5, "b": 0.9})
    assert list(restrict(rep, ["b"])["views"]) == ["b"]
    assert restrict(rep, None) is rep
    assert geo_score(restrict(rep, ["b"])) > geo_score(rep)
