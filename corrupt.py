"""Stage 2: controlled corruptions of a target's masks and depth maps.

A target folder (layout.py) holds what the checker treats as measurements: one depth map
per view in internal/depth.npz, where the silhouette is simply depth > 0. This script
writes a copy of the target with those measurements corrupted in a known, seeded way, so
the loop (refine.py) and the checker study (checker_eval.py) can run on it unchanged:

    uv run python corrupt.py data/generated/targets/fusion360 --kinds all --levels 1 2 3
    # -> data/generated/targets/fusion360_noisy/<kind>_L<level>/<part>/

What changes and what does not:
  * changed:   internal/depth.npz, renders/<view>_mask.png, renders/<view>_depth.png
  * unchanged: renders/<view>.png (the shaded RGB the agent looks at), gt.stl (offline
               scoring only), info.json normalisation, the folder name (= part name, so
               --init programs still match). In a real pipeline the photo is true and the
               masks / depth are what gets estimated (SAM 3, VGGT), so the noise goes there.
  * removed:   internal/view_weights.json (cached weights of the clean target)
  * added:     info.json["corruption"]: kind, level, parameters, seed, corrupted views and
               the measured error per view (mask IoU and depth MAE vs. the clean target).

Kinds and levels (512 px renders; depth is in normalised units, the part fits a unit
sphere about 3.5 units from the camera, so the part is ~2 units deep at most):

  kind         what happens, per view                                L1     L2     L3
  erode        silhouette boundary moves in by r px                  1      3      6
  dilate       silhouette boundary moves out by r px                 1      3      6
  jitter       boundary moves by a smooth random field, amplitude    2      4      8 px
  holes        n missing blobs inside the silhouette (radius ~ f*sqrt(area))
                                                                     2/.04  4/.07  6/.10
  blobs        n spurious blobs grown from the boundary              2/.04  4/.07  6/.10
  depth_noise  smooth random depth error, std sigma                  .005   .01    .02
  depth_scale  depth scaled by 1 +- e about the camera (sign per view)
                                                                     .5%    1%     2%
  bad_view     ONE view (seeded choice) shifted by s px, mask+depth  8      16     32

Every kind but bad_view hits all views. Pixels a mask gains take the depth of the nearest
observed pixel; pixels it loses get depth 0. Level 0 is the clean target.
"""
import argparse
import json
import shutil
import zlib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import layout

ROOT = Path(__file__).parent

LEVELS = {
    "erode": {1: {"r": 1}, 2: {"r": 3}, 3: {"r": 6}},
    "dilate": {1: {"r": 1}, 2: {"r": 3}, 3: {"r": 6}},
    "jitter": {1: {"amp": 2}, 2: {"amp": 4}, 3: {"amp": 8}},
    "holes": {1: {"n": 2, "f": 0.04}, 2: {"n": 4, "f": 0.07}, 3: {"n": 6, "f": 0.10}},
    "blobs": {1: {"n": 2, "f": 0.04}, 2: {"n": 4, "f": 0.07}, 3: {"n": 6, "f": 0.10}},
    "depth_noise": {1: {"sigma": 0.005}, 2: {"sigma": 0.01}, 3: {"sigma": 0.02}},
    "depth_scale": {1: {"e": 0.005}, 2: {"e": 0.01}, 3: {"e": 0.02}},
    "bad_view": {1: {"shift": 8}, 2: {"shift": 16}, 3: {"shift": 32}},
}
KINDS = list(LEVELS)
MASK_KINDS = ("erode", "dilate", "jitter", "holes", "blobs")
CORR_PX = 12      # correlation length of the smooth random fields (jitter, depth_noise)


# ------------------------------------------------------------------ helpers
def sdf(mask: np.ndarray) -> np.ndarray:
    """Signed distance to the silhouette boundary in px: >= 1 inside, <= -1 outside."""
    return ndimage.distance_transform_edt(mask) - ndimage.distance_transform_edt(~mask)


def with_mask(depth: np.ndarray, new_mask: np.ndarray) -> np.ndarray:
    """Depth map for a new silhouette: keep the observed depth where there is one, give
    pixels the mask gained the depth of the nearest observed pixel, 0 outside."""
    fg = depth > 0
    if not fg.any() or not new_mask.any():
        return np.zeros_like(depth)
    _, (ri, ci) = ndimage.distance_transform_edt(~fg, return_indices=True)
    return np.where(new_mask, depth[ri, ci], 0).astype(depth.dtype)


def smooth_field(shape, rng, corr=CORR_PX) -> np.ndarray:
    """Zero-mean, unit-std random field that varies over ~corr px."""
    f = ndimage.gaussian_filter(rng.standard_normal(shape), corr)
    return (f - f.mean()) / (f.std() + 1e-12)


def ellipses(shape, centers, radii, rng) -> np.ndarray:
    """Union of randomly stretched and rotated ellipses (bool mask)."""
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    out = np.zeros(shape, bool)
    for (cy, cx), r in zip(centers, radii):
        a, b = r * rng.uniform(0.6, 1.4), r * rng.uniform(0.6, 1.4)
        t = rng.uniform(0, np.pi)
        dy, dx = yy - cy, xx - cx
        u, v = dx * np.cos(t) + dy * np.sin(t), -dx * np.sin(t) + dy * np.cos(t)
        out |= (u / a) ** 2 + (v / b) ** 2 <= 1
    return out


def _pick(pixels: np.ndarray, n: int, rng) -> np.ndarray:
    """First n of a seeded shuffle, so a higher level keeps the lower level's picks."""
    return pixels[rng.permutation(len(pixels))[:n]]


# ------------------------------------------------------------------ one view
def corrupt_view(depth: np.ndarray, kind: str, level: int, rng) -> np.ndarray:
    """One depth map (0 = background) -> its corrupted version."""
    if level == 0:
        return depth.copy()
    p = LEVELS[kind][level]
    mask = depth > 0
    if not mask.any():
        return depth.copy()
    if kind == "erode":
        return with_mask(depth, sdf(mask) > p["r"])
    if kind == "dilate":
        return with_mask(depth, sdf(mask) >= -p["r"])
    if kind == "jitter":
        return with_mask(depth, sdf(mask) + p["amp"] * smooth_field(mask.shape, rng) > 0)
    if kind in ("holes", "blobs"):
        r = p["f"] * np.sqrt(mask.sum())
        if kind == "holes":
            seeds = _pick(np.argwhere(mask), p["n"], rng)
            return with_mask(depth, mask & ~ellipses(mask.shape, seeds, [r] * len(seeds), rng))
        edge = np.argwhere(mask & ~ndimage.binary_erosion(mask))
        seeds = _pick(edge, p["n"], rng)
        return with_mask(depth, mask | ellipses(mask.shape, seeds, [r] * len(seeds), rng))
    if kind == "depth_noise":
        noisy = depth + p["sigma"] * smooth_field(depth.shape, rng)
        return np.where(mask, np.maximum(noisy, 1e-3), 0).astype(depth.dtype)
    if kind == "depth_scale":
        s = 1.0 + p["e"] * rng.choice([-1.0, 1.0])
        return (depth * s).astype(depth.dtype)
    if kind == "bad_view":
        ang = rng.uniform(0, 2 * np.pi)
        dy, dx = p["shift"] * np.sin(ang), p["shift"] * np.cos(ang)
        return ndimage.shift(depth, (dy, dx), order=0, mode="constant", cval=0.0)
    raise ValueError(f"unknown corruption {kind!r}; choose from {KINDS}")


def view_error(clean: np.ndarray, noisy: np.ndarray) -> dict:
    """How far a corrupted view is from the clean one (for plots: the x-axis can be the
    actual measurement error instead of the level)."""
    a, b = clean > 0, noisy > 0
    union, inter = (a | b).sum(), (a & b).sum()
    err = np.abs(noisy[a & b] - clean[a & b])
    return {"mask_iou": float(inter / union) if union else 1.0,
            "depth_mae": float(err.mean()) if err.size else None}


# ------------------------------------------------------------------ one target
def rng_for(part: str, kind: str, seed: int, view: str = ""):
    """Same part + kind + seed -> same random draws, on any machine. The level is left out
    on purpose: L1..L3 share the blob positions, fields, signs and the bad view, so going
    up a level only makes the same corruption stronger."""
    key = zlib.crc32(f"{part}|{kind}|{view}".encode())
    return np.random.default_rng([seed, key])


def corrupt_depths(depths: dict, part: str, kind: str, level: int, seed=0):
    """{view: depth} -> ({view: corrupted depth}, [views that were corrupted])."""
    views = list(depths)
    if kind == "bad_view" and level > 0:
        hit = [views[int(rng_for(part, kind, seed).integers(len(views)))]]
    else:
        hit = views if level > 0 else []
    out = {v: (corrupt_view(depths[v], kind, level, rng_for(part, kind, seed, v))
               if v in hit else depths[v].copy()) for v in views}
    return out, hit


def corrupt_target(src: Path, dst: Path, kind: str, level: int, seed=0, force=False) -> dict:
    """Copy target `src` to `dst` with corrupted masks and depth. -> the corruption record."""
    from generate_solid import depth_preview
    src, dst = Path(src), Path(dst)
    if kind not in LEVELS:
        raise ValueError(f"unknown corruption {kind!r}; choose from {KINDS}")
    if dst.exists():
        if not force and layout.is_rendered(dst):
            return json.loads(layout.info(dst).read_text()).get("corruption", {})
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    layout.internal(dst, "view_weights.json").unlink(missing_ok=True)

    part = json.loads(layout.info(src).read_text()).get("part", src.name)
    with np.load(layout.depth(src)) as z:
        clean = {v: z[v] for v in z.files}
    noisy, hit = corrupt_depths(clean, part, kind, level, seed)
    np.savez_compressed(layout.depth(dst), **noisy)
    for v, d in noisy.items():
        Image.fromarray(((d > 0) * 255).astype(np.uint8)).save(layout.render(dst, v, "_mask"))
        Image.fromarray(depth_preview(d)).save(layout.render(dst, v, "_depth"))

    record = {"kind": kind, "level": level, "params": LEVELS[kind].get(level, {}),
              "seed": seed, "views": hit, "clean_target": str(src),
              "error": {v: view_error(clean[v], noisy[v]) for v in hit}}
    info = json.loads(layout.info(dst).read_text())
    info["corruption"] = record
    layout.info(dst).write_text(json.dumps(info, indent=2) + "\n")
    return record


def condition_name(kind: str, level: int) -> str:
    return "clean" if level == 0 else f"{kind}_L{level}"


# ------------------------------------------------------------------ preview sheet
def preview(src: Path, out_png: Path, view="iso_fr", kinds=None, levels=(1, 2, 3), seed=0,
            tile=160):
    """One picture for a part: rows = kinds, columns = levels, each tile the corrupted
    silhouette of `view` over the clean one (grey = both, red = lost, blue = gained) with
    the depth error inside. Nothing is written to disk except the PNG."""
    from PIL import ImageDraw
    from compare import depth_error_image
    kinds = kinds or KINDS
    part = Path(src).name
    with np.load(layout.depth(src)) as z:
        depths = {v: z[v] for v in z.files}
    clean = depths[view]
    m = clean > 0
    rows, cols = np.nonzero(m)
    pad = 40
    r0, r1 = max(rows.min() - pad, 0), min(rows.max() + pad, clean.shape[0])
    c0, c1 = max(cols.min() - pad, 0), min(cols.max() + pad, clean.shape[1])
    side = max(r1 - r0, c1 - c0)
    head = 18
    sheet = Image.new("RGB", (90 + tile * len(levels), head + tile * len(kinds)), "white")
    d = ImageDraw.Draw(sheet)
    for j, lv in enumerate(levels):
        d.text((90 + j * tile + 4, 3), f"level {lv}", fill="black")
    for i, k in enumerate(kinds):
        d.text((4, head + i * tile + tile // 2 - 6), k, fill="black")
        for j, lv in enumerate(levels):
            noisy, hit = corrupt_depths(depths, part, k, lv, seed)
            n = noisy[view]
            img = depth_error_image(m, clean, n > 0, n, vmax=0.05)[r0:r0 + side, c0:c0 + side]
            t = Image.fromarray(np.ascontiguousarray(img)).resize((tile - 4, tile - 4))
            if view not in hit:
                ImageDraw.Draw(t).text((4, 4), "(other view hit)", fill=(120, 120, 120))
            sheet.paste(t, (90 + j * tile + 2, head + i * tile + 2))
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    return out_png


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", type=Path,
                    help="a folder of target folders (e.g. data/generated/targets/fusion360)")
    ap.add_argument("--out", type=Path, help="default: <targets>_noisy next to it")
    ap.add_argument("--kinds", nargs="+", default=["all"], help=f"any of {KINDS} or all")
    ap.add_argument("--levels", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--split", type=Path, help="only the parts listed in this file")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="rebuild existing noisy targets")
    ap.add_argument("--preview", metavar="PART",
                    help="only write <out>/preview_<PART>.png (kinds x levels) and exit")
    ap.add_argument("--view", default="iso_fr", help="view shown by --preview")
    args = ap.parse_args(argv)

    kinds = KINDS if args.kinds == ["all"] else args.kinds
    bad = [k for k in kinds if k not in LEVELS]
    if bad:
        ap.error(f"unknown kinds {bad}; choose from {KINDS}")
    out = args.out or args.targets.with_name(args.targets.name + "_noisy")
    if args.preview:
        p = preview(args.targets / args.preview, out / f"preview_{args.preview}.png",
                    view=args.view, kinds=kinds, levels=args.levels, seed=args.seed)
        print(f"wrote {p}")
        return
    parts = sorted(p for p in args.targets.iterdir() if layout.is_rendered(p))
    if args.split:
        keep = set(args.split.read_text().split())
        parts = [p for p in parts if p.name in keep]
    parts = parts[:args.limit]
    if not parts:
        raise SystemExit(f"no rendered targets in {args.targets}")
    for k in kinds:
        for lv in args.levels:
            cond = out / condition_name(k, lv)
            errs = []
            for p in parts:
                rec = corrupt_target(p, cond / p.name, k, lv, args.seed, args.force)
                errs += [e["mask_iou"] for e in rec.get("error", {}).values()]
            print(f"{cond.name:16s} {len(parts)} parts   mean mask IoU vs clean "
                  f"{np.mean(errs) if errs else 1.0:.3f}   -> {cond}")


if __name__ == "__main__":
    main()
