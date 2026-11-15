"""Render every part in a split from the shared cameras, with seeded random poses.

usage: python render_views.py <split dev|test> [limit]
reads   data/deepcad/<split>/ids.txt, data/deepcad/cad_json/ (local only, never committed)
writes  data/deepcad/<split>/images/<part>/{rgb,mask}/<view>.png and depth.npz   (4 table views)
        data/deepcad/<split>/poses/<part>.json
        data/deepcad/<split>/meshes/<part>.{stl,step}   canonical ground truth (git-ignored)
        data/deepcad/<split>/meshes/<part>_table_posed.stl  ground truth in the render frame (git-ignored)
        data/cameras.json, data/deepcad/<split>/manifest.json

Pose (deterministic from SEED + part id):
  table views: a physically stable resting pose (trimesh.poses, sampled by stability
               probability) followed by a random spin about the vertical (+Z) axis.
  (The 6 "axis" views were dropped and archived; the axis rotation is still drawn so table poses are unchanged.)
Frames: x_render = R @ (scale * (x_canonical - centre)), with `centre` and `scale`
from the manifest. R is stored per set (3x3, row-major). `table_plane_z` is the z of the
table surface in the normalised render frame of the table set.
"""
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import trimesh
import trimesh.transformations as tf
import pyrender
from PIL import Image

import cadquery as cq
from cad_build import build_shape
import cameras

SEED = 2529
HERE = Path(__file__).parent
SRC = HERE / "deepcad" / "cad_json"


def to_mesh(shape):
    bb = shape.BoundingBox()
    diag = (bb.xlen ** 2 + bb.ylen ** 2 + bb.zlen ** 2) ** 0.5
    v, t = shape.tessellate(diag * 1e-3, 0.1)
    mesh = trimesh.Trimesh([(p.x, p.y, p.z) for p in v], np.array(t), process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def normalise(mesh):
    lo, hi = mesh.bounds
    centre = (lo + hi) / 2
    m = mesh.copy()
    m.apply_translation(-centre)
    r = np.linalg.norm(m.vertices, axis=1).max()  # bounding-sphere radius about the centre
    m.apply_scale(cameras.RADIUS / r)
    return m, centre, r


def pose_rotations(mesh_n, rng):
    """-> R_axis (3x3), R_table (3x3), table info dict. mesh_n is the normalised mesh."""
    r_axis = tf.random_rotation_matrix(rng.random(3))[:3, :3]
    info = {}
    try:
        transforms, probs = trimesh.poses.compute_stable_poses(mesh_n, n_samples=1)
        probs = np.asarray(probs, float)
        k = rng.choice(len(transforms), p=probs / probs.sum())
        r_stable = np.asarray(transforms[k])[:3, :3]
        info["stable_pose_index"] = int(k)
        info["stable_pose_prob"] = float(probs[k] / probs.sum())
    except Exception as e:  # fall back to the canonical orientation, and say so
        r_stable = np.eye(3)
        info["stable_pose_fallback"] = f"{type(e).__name__}: {e}"
    yaw = rng.uniform(0, 2 * np.pi)
    r_yaw = tf.rotation_matrix(yaw, [0, 0, 1])[:3, :3]
    r_table = r_yaw @ r_stable
    info["yaw_deg"] = float(np.degrees(yaw))
    info["table_plane_z"] = float((mesh_n.vertices @ r_table.T)[:, 2].min())
    return r_axis, r_table, info


def posed(mesh_n, rot):
    m = mesh_n.copy()
    m.apply_transform(np.block([[rot, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
    return m


def render_views(mesh_p, renderer, views):
    mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=(0.72, 0.74, 0.78, 1.0),
                                             metallicFactor=0.1, roughnessFactor=0.7)
    out = {}
    for name, v in views.items():
        scene = pyrender.Scene(bg_color=(1, 1, 1, 0), ambient_light=(0.35, 0.35, 0.35))
        scene.add(pyrender.Mesh.from_trimesh(mesh_p, material=mat, smooth=False))
        scene.add(pyrender.PerspectiveCamera(yfov=np.radians(cameras.YFOV_DEG), znear=0.05, zfar=20),
                  pose=v["pose"])
        scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=3.0), pose=v["pose"])  # headlight
        color, depth = renderer.render(scene)
        out[name] = (color[..., :3], depth)
    return out


def main():
    split = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    split_root = HERE / "deepcad" / split
    ids = [l.strip() for l in open(split_root / "ids.txt") if l.strip()][:limit]
    cameras.write_json(HERE / "cameras.json")
    views = cameras.views()
    groups = {g: {k: v for k, v in views.items() if v["group"] == g} for g in ("table",)}
    renderer = pyrender.OffscreenRenderer(cameras.IMG, cameras.IMG)
    out_root = split_root / "images"
    mesh_root = split_root / "meshes"
    mesh_root.mkdir(parents=True, exist_ok=True)
    (split_root / "poses").mkdir(parents=True, exist_ok=True)
    manifest, failed = {}, {}
    for pid in ids:
        name = pid.split("/")[1]
        try:
            shape = build_shape(SRC / f"{pid}.json")
            mesh = to_mesh(shape)
            cq.exporters.export(cq.Workplane(obj=shape), str(mesh_root / f"{name}.step"))
            mesh.export(mesh_root / f"{name}.stl")
            mesh_n, centre, r = normalise(mesh)
            rng = np.random.default_rng([SEED, int(name)])
            r_axis, r_table, tinfo = pose_rotations(mesh_n, rng)
            res = {}
            for g, rot in (("table", r_table),):
                mp = posed(mesh_n, rot)
                mp.export(mesh_root / f"{name}_{g}_posed.stl")
                res.update(render_views(mp, renderer, groups[g]))
        except Exception as e:  # report, never silently replace a part
            failed[pid] = f"{type(e).__name__}: {e}"
            traceback.print_exc()
            continue
        d = out_root / name
        (d / "rgb").mkdir(parents=True, exist_ok=True)
        (d / "mask").mkdir(parents=True, exist_ok=True)
        depths = {}
        for vname, (color, depth) in res.items():
            mask = depth > 0
            rgb = np.where(mask[..., None], color, 255).astype(np.uint8)
            Image.fromarray(rgb).save(d / "rgb" / f"{vname}.png")
            Image.fromarray((mask * 255).astype(np.uint8)).save(d / "mask" / f"{vname}.png")
            depths[vname] = depth.astype(np.float16)
        np.savez_compressed(d / "depth.npz", **depths)
        manifest[pid] = {"part": name, "centre": centre.tolist(), "scale": 1.0 / r,
                         "R_table": r_table.round(9).tolist(),
                         "table": tinfo, "n_triangles": int(len(mesh.faces)),
                         "watertight": bool(mesh.is_watertight)}
        (split_root / "poses" / f"{name}.json").write_text(cameras.pose_json(manifest[pid]), encoding="utf-8")
    json.dump({"split": split, "seed": SEED, "rendered": manifest, "failed": failed},
              open(split_root / "manifest.json", "w"), indent=2)
    print(f"{split}: rendered {len(manifest)} / {len(ids)}, failed {len(failed)}")


if __name__ == "__main__":
    main()
