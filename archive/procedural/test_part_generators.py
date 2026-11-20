"""Every generated part must be a valid single solid that matches its parameters."""
import math

import pytest

from generate_solid import check_solid, load_solid
from part_generators import GENERATORS, make_program

N = 40  # random parts per family


def build(tmp_path, family, i):
    params, src = make_program(family, seed=0, index=i)
    f = tmp_path / f"{family}_{i}.py"
    f.write_text(src)
    shape = load_solid(f)
    return params, shape, check_solid(shape)


def test_deterministic():
    assert make_program("bracket", 1, 7) == make_program("bracket", 1, 7)
    assert make_program("bracket", 1, 7) != make_program("bracket", 1, 8)


@pytest.mark.parametrize("family", list(GENERATORS))
def test_generated_parts_are_valid_single_solids(family, tmp_path):
    for i in range(N):
        params, shape, info = build(tmp_path, family, i)
        assert info["n_solids"] == 1, (family, i)


@pytest.mark.parametrize("i", range(N))
def test_plate_matches_its_parameters(i, tmp_path):
    p, shape, info = build(tmp_path, "plate", i)
    # outer size is exactly what was asked for (holes are inside, nothing sticks out)
    size = [hi - lo for lo, hi in zip(info["bbox_min"], info["bbox_max"])]
    assert size == pytest.approx([p["length"], p["width"], p["thickness"]], abs=1e-6)
    # exact volume = box - rounded corners - holes. This only holds if every hole
    # is fully inside the plate, so a hole that fell off the edge fails here.
    L, W, T, r = p["length"], p["width"], p["thickness"], p["corner_fillet"]
    n_grid = p["nx"] * p["ny"] if p["pattern"] in ("corners", "grid", "corners_center") else 0
    holes = n_grid * math.pi * (p["hole_d"] / 2) ** 2 + math.pi * (p["center_hole_d"] / 2) ** 2
    expected = (L * W - 4 * (r * r - math.pi * r * r / 4) - holes) * T
    assert info["volume"] == pytest.approx(expected, rel=1e-6), p
