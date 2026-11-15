"""Geometric checker: how close is a candidate part to a target part, view by view?

Both parts must be rendered with the same rig AND in the same frame, otherwise a
part twice the size would look identical. Render the candidate with --like:

    uv run python generate_solid.py target.py    --out out/target
    uv run python generate_solid.py candidate.py --out out/cand --like out/target
    uv run python compare.py out/target out/cand              # -> out/cand/compare/

Per view it measures
  * silhouette IoU   = |target AND candidate| / |target OR candidate|   (1 = same outline)
  * depth error      = |depth_cand - depth_target| on pixels both cover, as mean (MAE),
                       RMSE and 95th percentile, in normalised units and in mm
and writes, per view,
  * <view>_overlay.png  grey = both, RED = missing material (in target, not candidate),
                        BLUE = extra material (in candidate, not target)
  * <view>_depth_err.png heatmap of the depth error where both cover (pale = 0,
                        dark = >= --depth-vmax), uncovered pixels shown like the overlay
plus summary.png (all views side by side) and report.json.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BG = (255, 255, 255)
BOTH = (200, 200, 200)
MISSING = (215, 38, 38)     # red: target has material here, candidate doesn't
EXTRA = (38, 98, 215)       # blue: candidate has material here, target doesn't

# pale yellow -> orange -> red -> dark purple   (low error -> high error)
_STOPS = np.array([[255, 247, 188], [254, 196, 79], [236, 112, 20], [189, 0, 38], [84, 0, 60]],
                  dtype=np.float64)


def colormap(t):
    """t in [0, 1] (any shape) -> uint8 RGB."""
    t = np.clip(t, 0, 1) * (len(_STOPS) - 1)
    i = np.minimum(t.astype(int), len(_STOPS) - 2)
    f = (t - i)[..., None]
    return (_STOPS[i] * (1 - f) + _STOPS[i + 1] * f).round().astype(np.uint8)


# ------------------------------------------------------------------ metrics
def view_metrics(mask_t, depth_t, mask_c, depth_c, mm_per_unit=1.0):
    """All the numbers for one view. Masks are bool, depths float (0 = background)."""
    inter = mask_t & mask_c
    union = mask_t | mask_c
    m = {
        "iou": float(inter.sum() / union.sum()) if union.any() else 1.0,
        "missing_px": int((mask_t & ~mask_c).sum()),
        "extra_px": int((mask_c & ~mask_t).sum()),
        "target_px": int(mask_t.sum()),
        "candidate_px": int(mask_c.sum()),
    }
    if inter.any():
        err = np.abs(depth_c[inter] - depth_t[inter]).astype(np.float64)
        m.update(depth_mae=float(err.mean()), depth_rmse=float(np.sqrt((err ** 2).mean())),
                 depth_p95=float(np.percentile(err, 95)))
    else:  # nothing in common: depth error is undefined
        m.update(depth_mae=None, depth_rmse=None, depth_p95=None)
    for k in ("depth_mae", "depth_rmse", "depth_p95"):
        m[k + "_mm"] = None if m[k] is None else m[k] * mm_per_unit
    return m


# ------------------------------------------------------------------ images
def overlay_image(mask_t, mask_c):
    img = np.empty(mask_t.shape + (3,), np.uint8)
    img[:] = BG
    img[mask_t & mask_c] = BOTH
    img[mask_t & ~mask_c] = MISSING
    img[mask_c & ~mask_t] = EXTRA
    return img


def depth_error_image(mask_t, depth_t, mask_c, depth_c, vmax):
    img = overlay_image(mask_t, mask_c)
    # dim the red/blue so the heatmap is what stands out
    for sel, col in ((mask_t & ~mask_c, MISSING), (mask_c & ~mask_t, EXTRA)):
        img[sel] = (np.array(col) * 0.35 + np.array(BG) * 0.65).astype(np.uint8)
    inter = mask_t & mask_c
    img[inter] = colormap(np.abs(depth_c[inter] - depth_t[inter]) / vmax)
    return img


def _label(img, lines):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        d.text((6, 5 + 12 * i), line, fill=(0, 0, 0))
    return im


def _legend(width, vmax, mm_per_unit):
    h = 40
    im = Image.new("RGB", (width, h), BG)
    d = ImageDraw.Draw(im)
    x = 6
    for col, txt in ((BOTH, "both"), (MISSING, "missing (target only)"), (EXTRA, "extra (candidate only)")):
        d.rectangle([x, 6, x + 12, 18], fill=col)
        d.text((x + 16, 6), txt, fill=(0, 0, 0))
        x += 22 + 7 * len(txt)
    bar_x, bar_w = x + 10, 160
    if bar_x + bar_w + 120 < width:
        ramp = colormap(np.linspace(0, 1, bar_w))[None].repeat(12, 0)
        im.paste(Image.fromarray(ramp), (bar_x, 6))
        d.text((bar_x - 2, 22), "0", fill=(0, 0, 0))
        d.text((bar_x + bar_w - 60, 22), f">= {vmax * mm_per_unit:.2f} mm", fill=(0, 0, 0))
        d.text((bar_x + bar_w + 8, 6), "depth error", fill=(0, 0, 0))
    return im


# ------------------------------------------------------------------ io
def load_views(run_dir: Path):
    """-> ({view: (mask, depth)}, info) from a generate_solid.py output directory."""
    info = json.loads((run_dir / "info.json").read_text())
    depth = np.load(run_dir / "depth.npz")
    views = {v: (depth[v] > 0, depth[v]) for v in info["views"]}
    return views, info


def compare(target_dir: Path, cand_dir: Path, out: Path, depth_vmax=0.05, thumb=256):
    tv, tinfo = load_views(target_dir)
    cv, cinfo = load_views(cand_dir)
    if tinfo["normalization"] != cinfo["normalization"]:
        print("warning: target and candidate were rendered in different frames; render the "
              "candidate with `generate_solid.py ... --like <target dir>` for a fair comparison",
              file=sys.stderr)
    missing = set(tv) - set(cv)
    if missing:
        raise ValueError(f"candidate has no renders for views {sorted(missing)}")
    mm = 1.0 / tinfo["normalization"]["scale"]   # normalised units -> target's mm
    out.mkdir(parents=True, exist_ok=True)

    per_view, tiles = {}, []
    for v, (mt, dt) in tv.items():
        mc, dc = cv[v]
        m = view_metrics(mt, dt, mc, dc, mm)
        per_view[v] = m
        ov = overlay_image(mt, mc)
        de = depth_error_image(mt, dt, mc, dc, depth_vmax)
        Image.fromarray(ov).save(out / f"{v}_overlay.png")
        Image.fromarray(de).save(out / f"{v}_depth_err.png")
        dtxt = "depth n/a" if m["depth_mae"] is None else f"depth MAE {m['depth_mae_mm']:.2f} mm"
        small = lambda a: np.asarray(Image.fromarray(a).resize((thumb, thumb), Image.NEAREST))
        tiles.append((_label(small(ov), [v, f"IoU {m['iou']:.3f}"]), _label(small(de), [v, dtxt])))

    depths = [m["depth_mae"] for m in per_view.values() if m["depth_mae"] is not None]
    worst = min(per_view, key=lambda v: per_view[v]["iou"])
    report = {
        "target": str(target_dir), "candidate": str(cand_dir),
        "mean_iou": float(np.mean([m["iou"] for m in per_view.values()])),
        "min_iou": per_view[worst]["iou"], "worst_view": worst,
        "mean_depth_mae": float(np.mean(depths)) if depths else None,
        "mean_depth_mae_mm": float(np.mean(depths)) * mm if depths else None,
        "mm_per_unit": mm, "depth_vmax": depth_vmax,
        "views": per_view,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")

    # summary sheet: row 1 = overlays, row 2 = depth heatmaps, legend underneath
    n = len(tiles)
    legend = _legend(n * thumb, depth_vmax, mm)
    sheet = Image.new("RGB", (n * thumb, 2 * thumb + legend.height), BG)
    for i, (ov, de) in enumerate(tiles):
        sheet.paste(ov, (i * thumb, 0))
        sheet.paste(de, (i * thumb, thumb))
    sheet.paste(legend, (0, 2 * thumb))
    sheet.save(out / "summary.png")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", type=Path, help="generate_solid.py output dir of the target")
    ap.add_argument("candidate", type=Path, help="... of the candidate (rendered with --like target)")
    ap.add_argument("--out", type=Path, default=None, help="default: <candidate>/compare")
    ap.add_argument("--depth-vmax", type=float, default=0.05,
                    help="depth error (normalised units) shown as the darkest colour")
    args = ap.parse_args()
    r = compare(args.target, args.candidate, args.out or args.candidate / "compare", args.depth_vmax)
    print(f"{'view':10s} {'IoU':>6s} {'missing':>8s} {'extra':>7s} {'depth MAE mm':>13s}")
    for v, m in r["views"].items():
        d = "n/a" if m["depth_mae_mm"] is None else f"{m['depth_mae_mm']:.3f}"
        print(f"{v:10s} {m['iou']:6.3f} {m['missing_px']:8d} {m['extra_px']:7d} {d:>13s}")
    d = "n/a" if r["mean_depth_mae_mm"] is None else f"{r['mean_depth_mae_mm']:.3f} mm"
    print(f"mean IoU {r['mean_iou']:.3f} (worst: {r['worst_view']} {r['min_iou']:.3f}), "
          f"mean depth MAE {d}")


if __name__ == "__main__":
    main()
