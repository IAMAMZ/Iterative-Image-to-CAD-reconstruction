"""Fusion360 targets, cadrille starting programs, placement and 3D evaluation."""
import json
from pathlib import Path

import numpy as np
import pytest
import trimesh

from cadrille_init import fit_scale, placement_code, to_refine_program
from compare import compare
from conftest import PART
from eval3d import evaluate
from generate_solid import render_mesh
from rig import load_rig
from view_weights import measure_bbox, view_weights

ROOT = Path(__file__).resolve().parents[1]
CADRILLE_PY = ROOT / "cadrille" / "work_dirs" / "f360_rl" / "py"
CADRILLE_SCORES = ROOT / "cadrille" / "work_dirs" / "f360_rl" / "scores.json"


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


def test_tuning_set_is_disjoint_from_the_evaluation_split():
    d = ROOT / "data" / "fusion360"
    stage1, tuning = set((d / "stage1.txt").read_text().split()), set((d / "tuning.txt").read_text().split())
    assert len(stage1) == 60 and len(tuning) == 9 and not stage1 & tuning
    meta = json.loads((d / "tuning_meta.json").read_text())["parts"]
    assert {r["iou_bin"] for r in meta.values()} == {"low", "mid", "high"}
