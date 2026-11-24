"""Forward-rendering geometric check: score a candidate against the target views and
decide whether an edit is kept.

Inputs are compare.py reports (per-view silhouette IoU and the union-based, capped depth
error `depth_err`, defined even when the outlines barely overlap) and, optionally,
per-view confidence weights from view_weights.py. Views that disagree with the others
(low weight) count less in the score and cannot veto an edit on their own.
`signal` selects what the check looks at (ablation `--geo-signal`): "both" (silhouette IoU
and depth error, the main method), "mask" (silhouette only) or "depth" (depth error only;
note `depth_err` is union-based, so it still carries the outline implicitly).
No 3D ground truth is used anywhere in here.
"""
import numpy as np

TRUSTED = 0.5   # views with a weight below this are ignored by the per-view drop guard
SIGNALS = ("both", "mask", "depth")


def restrict(report, views):
    """The report seen through a subset of views (ablation `--views worst`); None = all."""
    if views is None:
        return report
    return {**report, "views": {v: report["views"][v] for v in views}}


def _weights(report, weights):
    views = list(report["views"])
    if weights is None:
        return views, np.ones(len(views))
    return views, np.array([float(weights.get(v, 1.0)) for v in views])


def _depth_term(m):
    """The score's per-view depth error: compare.py's union-based, capped `depth_err`
    (old reports without it fall back to the MAE on the overlap)."""
    return m["depth_err"] if "depth_err" in m else m.get("depth_mae")


def weighted_means(report, weights=None):
    """-> (weighted mean silhouette IoU, weighted mean depth error or None)."""
    views, w = _weights(report, weights)
    if w.sum() <= 0:
        w = np.ones(len(views))
    iou = np.array([report["views"][v]["iou"] for v in views])
    m_iou = float((w * iou).sum() / w.sum())
    d = [(wi, _depth_term(report["views"][v])) for v, wi in zip(views, w)]
    d = [(wi, x) for wi, x in d if x is not None]
    dw = sum(wi for wi, _ in d)
    m_d = float(sum(wi * x for wi, x in d) / dw) if d and dw > 0 else None
    return m_iou, m_d


def geo_score(report, weights=None, depth_weight=1.0, signal="both"):
    """Higher is better: weighted silhouette IoU minus weighted depth error ("both"), the
    IoU alone ("mask") or minus the depth error alone ("depth")."""
    m_iou, m_d = weighted_means(report, weights)
    d = 1.0 if m_d is None else m_d
    if signal == "mask":
        return m_iou
    if signal == "depth":
        return -depth_weight * d
    return m_iou - depth_weight * d


def _view_change(cur_m, new_m, signal):
    """Per-view change, higher = better: IoU change, or for "depth" the fall in depth error."""
    if signal == "depth":
        a, b = _depth_term(cur_m), _depth_term(new_m)
        return 0.0 if a is None or b is None else a - b
    return new_m["iou"] - cur_m["iou"]


def geo_accept(cur, new, weights=None, min_gain=1e-3, max_view_drop=0.05, signal="both"):
    """Keep an edit only if the weighted score improves by more than min_gain and (unless
    signal == "depth") no trusted view's IoU drops by more than max_view_drop.
    -> (keep, details); details["inconclusive"] is True when |gain| <= min_gain;
    worst_view / worst_view_drop are in IoU, or in depth error for signal "depth"."""
    gain = geo_score(new, weights, signal=signal) - geo_score(cur, weights, signal=signal)
    views = [v for v in cur["views"]
             if weights is None or float(weights.get(v, 1.0)) >= TRUSTED]
    drops = {v: _view_change(cur["views"][v], new["views"][v], signal) for v in views}
    worst = min(drops, key=drops.get) if drops else None
    drop = drops[worst] if worst else 0.0
    guard = signal != "depth"
    keep = gain > min_gain and (not guard or drop >= -max_view_drop)
    return keep, {"gain": gain, "worst_view_drop": drop, "worst_view": worst,
                  "inconclusive": abs(gain) <= min_gain, "keep": keep, "signal": signal}


def residual_table(report, weights=None, signal="both"):
    """Per-view table for the agent; only the columns of the active signal."""
    mask, depth = signal in ("both", "mask"), signal in ("both", "depth")
    head = f"{'view':8s} {'weight':>6s}"
    if mask:
        head += f" {'IoU':>5s} {'missing px':>10s} {'extra px':>9s}"
    if depth:
        head += f" {'depth MAE':>9s}"
    rows = [head]
    mm = report.get("mm_per_unit", 1.0)
    for v, m in report["views"].items():
        w = 1.0 if weights is None else float(weights.get(v, 1.0))
        row = f"{v:8s} {w:6.2f}"
        if mask:
            row += f" {m['iou']:5.3f} {m['missing_px']:10d} {m['extra_px']:9d}"
        if depth:
            d = "n/a" if m["depth_mae"] is None else f"{m['depth_mae'] * mm:.2f}"
            row += f" {d:>9s}"
        rows.append(row)
    return "\n".join(rows)
