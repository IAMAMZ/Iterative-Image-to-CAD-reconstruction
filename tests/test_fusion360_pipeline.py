"""Fusion360 targets, cadrille starting programs, placement and 3D evaluation."""
import json
from pathlib import Path

import numpy as np
import pytest
import trimesh

from cadrille_init import (cube_rotations, fit_placement, fit_scale, placement_code,
                           to_refine_program)
from compare import compare
from conftest import PART
from eval3d import evaluate
from generate_solid import render_mesh
from rig import load_rig
from view_weights import measure_bbox, view_weights

ROOT = Path(__file__).resolve().parents[1]
CADRILLE_PY = ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "py"
CADRILLE_SCORES = ROOT / "cadrille" / "work_dirs" / "f360_rl_test" / "scores.json"


def _as_candidate(mesh, target, out):
    """Render a mesh as a candidate in the target's frame (what --like does)."""
    norm = json.loads((target / "internal" / "info.json").read_text())["normalization"]
    render_mesh(mesh, out, load_rig(), norm)
    mesh.export(out / "solid.stl")
    return out


def test_target_layout_and_frame(f360_target):
    info = json.loads((f360_target / "internal" / "info.json").read_text())
    assert set(info["views"]) == {c["name"] for c in load_rig()["cameras"]}
    gt = trimesh.load(f360_target / "gt.stl")
    assert gt.extents.max() == pytest.approx(200.0, rel=1e-6)       # cadrille's frame
    assert np.allclose((gt.bounds[0] + gt.bounds[1]) / 2, 0, atol=1e-6)
    lo, hi = measure_bbox(f360_target, load_rig())                   # from depth maps only
    assert np.allclose(hi - lo, gt.extents, atol=2.0)


def test_gt_as_candidate_is_perfect(f360_target, tmp_path):
    gt = trimesh.load(f360_target / "gt.stl")
    cand = _as_candidate(gt, f360_target, tmp_path / "cand")
    rep = compare(f360_target, cand, tmp_path / "cmp")
    assert min(m["iou"] for m in rep["views"].values()) > 0.99
    e = evaluate(f360_target, cand)
    assert e["iou3d"] > 0.99 and e["iou3d_cad"] > 0.99 and e["f1"] > 0.99


def test_clean_target_views_are_trusted(f360_target):
    w = view_weights(f360_target, cache=False)
    assert min(w.values()) > 0.95


def test_cadrille_program_builds_and_matches_cadrille_score(f360_target, tmp_path):
    from refine import build
    src = to_refine_program((CADRILLE_PY / f"{PART}.py").read_text())
    err = build(src, tmp_path / "init", f360_target, (0.0, 0.0, 0.0))
    assert err is None, err
    e = evaluate(f360_target, tmp_path / "init")
    ref = {r["id"]: r for r in json.loads(CADRILLE_SCORES.read_text())}[PART]
    assert e["iou3d_cad"] == pytest.approx(ref["iou"], abs=0.02)


def test_placement_code_runs(f360_target, tmp_path):
    from refine import build
    src = to_refine_program((CADRILLE_PY / f"{PART}.py").read_text()) + placement_code(0.9)
    assert build(src, tmp_path / "c", f360_target, (0.0, 0.0, 0.0)) is None
    info = json.loads((tmp_path / "c" / "internal" / "info.json").read_text())
    size = np.array(info["bbox_max"]) - np.array(info["bbox_min"])
    assert size.max() == pytest.approx(0.9 * 200, rel=0.03)


def test_fit_scale_recovers_a_known_scale(f360_target):
    gt = trimesh.load(f360_target / "gt.stl")
    small = gt.copy()
    small.apply_scale(0.8)
    s, fitted, unscaled = fit_scale(small, f360_target, load_rig())
    assert s == pytest.approx(1.25, rel=0.02)
    assert fitted > unscaled


def test_cube_rotations_are_the_24_proper_ones():
    rots = cube_rotations()
    assert len(rots) == 24 and rots[0][1] == (0, 0, 0)
    assert np.array_equal(rots[0][0], np.eye(3))
    for R, _ in rots:
        assert round(np.linalg.det(R)) == 1 and np.array_equal(R @ R.T, np.eye(3))


@pytest.mark.parametrize("i", [1, 5, 13, 23])
def test_rotation_code_turns_the_solid_like_its_matrix(i):
    """The CadQuery placement code rotates the solid exactly as the matrix fit_placement
    scored (an asymmetric L-shape, so a wrong turn moves its centre of mass)."""
    import cadquery as cq
    R, turns = cube_rotations()[i]
    base = ("import cadquery as cq\n"
            "r = cq.Workplane().box(60, 30, 10).union("
            "cq.Workplane().box(10, 10, 40).translate((25, 10, 20)))\nresult = r\n")
    env = {}
    exec(base, env)
    c0 = np.array(env["result"].val().Center().toTuple())
    env = {}
    exec(base + placement_code(1.0, turns), env)
    c1 = np.array(env["result"].val().Center().toTuple())
    assert np.allclose(c1, R @ c0, atol=1e-6), (turns, c0, c1)


def test_fit_placement_undoes_a_wrong_rotation(f360_target):
    gt = trimesh.load(f360_target / "gt.stl")
    rig = load_rig()
    R_wrong = cube_rotations()[7][0]
    turned = gt.copy()
    T = np.eye(4)
    T[:3, :3] = R_wrong
    turned.apply_transform(T)
    fit = fit_placement(turned, f360_target, rig)
    assert fit["turns"] != (0, 0, 0)
    assert fit["score"] > fit["score_identity"] + 0.05         # clearly better than as given
    assert fit["score"] > 0.95                                   # about as good as the GT itself
    assert fit["scale"] == pytest.approx(1.0, abs=0.02)


def test_fit_placement_keeps_a_correct_orientation(f360_target):
    gt = trimesh.load(f360_target / "gt.stl")
    fit = fit_placement(gt, f360_target, load_rig())
    assert fit["turns"] == (0, 0, 0)
    assert fit["scale"] == pytest.approx(1.0, abs=0.02)


def test_tuning_set_is_disjoint_from_the_evaluation_split():
    d = ROOT / "data" / "fusion360"
    stage1, tuning = set((d / "stage1.txt").read_text().split()), set((d / "tuning.txt").read_text().split())
    assert len(stage1) == 60 and len(tuning) == 9 and not stage1 & tuning
    meta = json.loads((d / "tuning_meta.json").read_text())["parts"]
    assert {r["iou_bin"] for r in meta.values()} == {"low", "mid", "high"}
