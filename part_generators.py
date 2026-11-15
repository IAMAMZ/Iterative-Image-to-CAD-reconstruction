"""Random generators for simple parts. Each one writes a CadQuery program.

Every generator takes a random.Random and returns (params, program_source).
The program is plain CadQuery code with the numbers written in, ending in
`result = ...`, so it can be run by generate_solid.py like any other part file.

    uv run python part_generators.py --n 5                       # 5 of each family
    uv run python part_generators.py --family bracket --n 10 --seed 3

Output: out/parts/<family>_<NNN>/{part.py, params.json, ...renders from generate_solid}
All sizes are in mm and rounded to 0.5 mm so programs stay readable.
"""
import argparse
import json
import random
import sys
from pathlib import Path


def _r(x, step=0.5):
    """Round to a readable step (0.5 mm)."""
    return round(round(x / step) * step, 3)


def _fmt(pts):
    return "[" + ", ".join(f"({x:g}, {y:g})" for x, y in pts) + "]"


# --------------------------------------------------------------------------- plate
def plate(rng: random.Random):
    """Rectangular plate with a hole pattern and optionally rounded corners."""
    L = _r(rng.uniform(40, 120))
    W = _r(rng.uniform(30, min(L, 90)))
    T = _r(rng.uniform(3, 12))
    pattern = rng.choice(["corners", "grid", "center", "corners_center"])
    d = _r(rng.uniform(3, min(10, W / 5)))
    m = _r(max(d * 1.2, rng.uniform(d, W / 4)))          # edge margin to hole centres
    nx, ny = (rng.randint(2, 4), rng.randint(2, 3)) if pattern == "grid" else (2, 2)
    # grid holes must not touch each other
    while nx > 2 and (L - 2 * m) / (nx - 1) < 2 * d:
        nx -= 1
    while ny > 2 and (W - 2 * m) / (ny - 1) < 2 * d:
        ny -= 1
    fillet = _r(rng.uniform(1, m - d / 2)) if rng.random() < 0.6 and m - d / 2 > 1.5 else 0.0

    lines = [f'result = cq.Workplane("XY").box({L:g}, {W:g}, {T:g})']
    if fillet:
        lines.append(f'result = result.edges("|Z").fillet({fillet:g})')
    top = 'result.faces(">Z").workplane()'
    if pattern in ("corners", "corners_center", "grid"):
        # rarray takes the spacing *between neighbouring holes*, not the total span
        sx, sy = round((L - 2 * m) / (nx - 1), 3), round((W - 2 * m) / (ny - 1), 3)
        lines.append(f"result = {top}.rarray({sx:g}, {sy:g}, {nx}, {ny}).hole({d:g})")
    dc = 0.0
    if pattern in ("center", "corners_center"):
        dc = _r(min(rng.uniform(d, 3 * d), (W - 2 * m) * 0.6, (L - 2 * m) * 0.6)) \
            if pattern == "corners_center" else _r(rng.uniform(d, W / 2))
        lines.append(f"result = {top}.hole({dc:g})")
    params = dict(family="plate", length=L, width=W, thickness=T, pattern=pattern,
                  hole_d=d, margin=m, nx=nx, ny=ny, center_hole_d=dc, corner_fillet=fillet)
    return params, "\n".join(lines)


# --------------------------------------------------------------------------- bracket
def bracket(rng: random.Random):
    """L-bracket: a base leg and an upright leg, two holes in each, optional gusset."""
    T = _r(rng.uniform(3, 10))
    L = _r(rng.uniform(30, 80))          # base length (x)
    H = _r(rng.uniform(25, 80))          # upright height (z)
    W = _r(rng.uniform(25, 70))          # width (y)
    d = _r(rng.uniform(3, min(10, 0.4 * (L - T), 0.4 * (H - T), 0.35 * W)))
    gusset = rng.random() < 0.5
    g_t = _r(min(T, W / 2 - d - 2)) if gusset else 0.0   # gusset thickness, clear of holes
    if g_t < 2:
        gusset, g_t = False, 0.0
    g_len = _r(0.6 * min(L - T, H - T)) if gusset else 0.0

    y = _r(W / 4)
    xb, zu = _r((T + L) / 2), _r((T + H) / 2)
    if gusset:  # keep holes beyond the gusset so they don't cut into it
        xb, zu = _r(max(xb, T + g_len * 0.5 + d)), _r(max(zu, T + g_len * 0.5 + d))
        xb, zu = min(xb, L - d), min(zu, H - d)
    profile = [(0, 0), (L, 0), (L, T), (T, T), (T, H), (0, H)]
    lines = [
        "# L profile drawn in the XZ plane, extruded symmetrically along Y",
        f'result = cq.Workplane("XZ").polyline({_fmt(profile)}).close().extrude({W / 2:g}, both=True)',
    ]
    if gusset:
        tri = [(T, T), (T + g_len, T), (T, T + g_len)]
        lines.append(f'gusset = cq.Workplane("XZ").polyline({_fmt(tri)}).close().extrude({g_t / 2:g}, both=True)')
        lines.append("result = result.union(gusset)")
    lines += [
        f'base_holes = cq.Workplane("XY").pushPoints({_fmt([(xb, -y), (xb, y)])}).circle({d / 2:g}).extrude({T:g})',
        f'upright_holes = cq.Workplane("YZ").pushPoints({_fmt([(-y, zu), (y, zu)])}).circle({d / 2:g}).extrude({T:g})',
        "result = result.cut(base_holes).cut(upright_holes)",
    ]
    params = dict(family="bracket", base_length=L, height=H, width=W, thickness=T, hole_d=d,
                  gusset=gusset, gusset_thickness=g_t, gusset_length=g_len)
    return params, "\n".join(lines)


# --------------------------------------------------------------------------- stepped block
def stepped_block(rng: random.Random):
    """Block made of 2-4 steps getting lower along X, optional hole through some steps."""
    n = rng.randint(2, 4)
    W = _r(rng.uniform(20, 60))
    lengths = [_r(rng.uniform(10, 35)) for _ in range(n)]
    heights = sorted((_r(rng.uniform(5, 50)) for _ in range(n)), reverse=True)
    for i in range(1, n):  # each step at least 3 mm lower than the previous one
        heights[i] = min(heights[i], heights[i - 1] - 3)
    heights = [max(h, 2.0 + 3 * (n - 1 - i)) for i, h in enumerate(heights)]

    xs = [0.0]
    for l in lengths:
        xs.append(_r(xs[-1] + l))
    profile = [(0, 0), (xs[-1], 0)]
    for i in reversed(range(n)):   # walk back along the top of the steps
        profile += [(xs[i + 1], heights[i]), (xs[i], heights[i])]
    profile = [p for i, p in enumerate(profile) if i == 0 or p != profile[i - 1]]

    lines = [
        "# step profile drawn in the XZ plane, extruded symmetrically along Y",
        f'result = cq.Workplane("XZ").polyline({_fmt(profile)}).close().extrude({W / 2:g}, both=True)',
    ]
    holes = []
    for i in range(n):
        if rng.random() < 0.4:
            d = _r(rng.uniform(3, 0.5 * min(lengths[i], W)))
            cx = _r((xs[i] + xs[i + 1]) / 2)
            holes.append({"step": i, "x": cx, "d": d})
            lines.append(f'result = result.cut(cq.Workplane("XY").center({cx:g}, 0)'
                         f'.circle({d / 2:g}).extrude({heights[i]:g}))')
    params = dict(family="stepped_block", n_steps=n, width=W, step_lengths=lengths,
                  step_heights=heights, holes=holes)
    return params, "\n".join(lines)


GENERATORS = {"plate": plate, "bracket": bracket, "stepped_block": stepped_block}


def make_program(family: str, seed: int, index: int):
    """Deterministic: the same (family, seed, index) always gives the same part."""
    rng = random.Random(f"{family}-{seed}-{index}")
    params, body = GENERATORS[family](rng)
    params.update(seed=seed, index=index)
    header = f"# {family} #{index} (seed {seed}), generated by part_generators.py\nimport cadquery as cq\n\n"
    return params, header + body + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--family", choices=[*GENERATORS, "all"], default="all")
    ap.add_argument("--n", type=int, default=5, help="parts per family")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("out/parts"))
    ap.add_argument("--no-render", action="store_true", help="only write the programs")
    args = ap.parse_args()

    from generate_solid import generate   # imported here so --no-render stays light
    from rig import load_rig
    rig = load_rig()

    families = list(GENERATORS) if args.family == "all" else [args.family]
    failed = []
    for fam in families:
        for i in range(args.n):
            params, src = make_program(fam, args.seed, i)
            d = args.out / f"{fam}_{i:03d}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "part.py").write_text(src)
            (d / "params.json").write_text(json.dumps(params, indent=2) + "\n")
            if args.no_render:
                continue
            try:
                generate(d / "part.py", d, rig)
                print(f"ok    {d}")
            except Exception as e:
                failed.append(d)
                print(f"FAIL  {d}: {type(e).__name__}: {e}")
    if failed:
        sys.exit(f"{len(failed)} part(s) failed")


if __name__ == "__main__":
    main()
