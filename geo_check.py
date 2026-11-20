"""Forward-rendering geometric check: score a candidate against the target views and
decide whether an edit is kept.

Inputs are compare.py reports (per-view silhouette IoU and depth error) and, optionally,
per-view confidence weights from view_weights.py. Views that disagree with the others
(low weight) count less in the score and cannot veto an edit on their own.
No 3D ground truth is used anywhere in here.
"""
import numpy as np

TRUSTED = 0.5   # views with a weight below this are ignored by the per-view drop guard


def _weights(report, weights):
    views = list(report["views"])
    if weights is None:
        return views, np.ones(len(views))
    return views, np.array([float(weights.get(v, 1.0)) for v in views])


def weighted_means(report, weights=None):
    """-> (weighted mean silhouette IoU, weighted mean depth MAE or None)."""
    views, w = _weights(report, weights)
    if w.sum() <= 0:
        w = np.ones(len(views))
    iou = np.array([report["views"][v]["iou"] for v in views])
    m_iou = float((w * iou).sum() / w.sum())
    d = [(wi, report["views"][v]["depth_mae"]) for v, wi in zip(views, w)
         if report["views"][v]["depth_mae"] is not None]
    dw = sum(wi for wi, _ in d)
    m_d = float(sum(wi * x for wi, x in d) / dw) if d and dw > 0 else None
    return m_iou, m_d


def geo_score(report, weights=None, depth_weight=1.0):
    """Higher is better: weighted silhouette IoU minus weighted depth error."""
    m_iou, m_d = weighted_means(report, weights)
    return m_iou - depth_weight * (1.0 if m_d is None else m_d)


def geo_accept(cur, new, weights=None, min_gain=1e-3, max_view_drop=0.05):
    """Keep an edit only if the weighted silhouette+depth score improves by more than
    min_gain and no trusted view's IoU drops by more than max_view_drop.
    -> (keep, details); details["inconclusive"] is True when |gain| <= min_gain."""
    gain = geo_score(new, weights) - geo_score(cur, weights)
    views = [v for v in cur["views"]
             if weights is None or float(weights.get(v, 1.0)) >= TRUSTED]
    drops = {v: new["views"][v]["iou"] - cur["views"][v]["iou"] for v in views}
    worst = min(drops, key=drops.get) if drops else None
    drop = drops[worst] if worst else 0.0
    keep = gain > min_gain and drop >= -max_view_drop
    return keep, {"gain": gain, "worst_view_drop": drop, "worst_view": worst,
                  "inconclusive": abs(gain) <= min_gain, "keep": keep}


def residual_table(report, weights=None):
    rows = [f"{'view':8s} {'weight':>6s} {'IoU':>5s} {'missing px':>10s} {'extra px':>9s} "
            f"{'depth MAE':>9s}"]
    mm = report.get("mm_per_unit", 1.0)
    for v, m in report["views"].items():
        d = "n/a" if m["depth_mae"] is None else f"{m['depth_mae'] * mm:.2f}"
        w = 1.0 if weights is None else float(weights.get(v, 1.0))
        rows.append(f"{v:8s} {w:6.2f} {m['iou']:5.3f} {m['missing_px']:10d} {m['extra_px']:9d} "
                    f"{d:>9s}")
    return "\n".join(rows)
