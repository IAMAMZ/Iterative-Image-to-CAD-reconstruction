"""Render the Fusion360 test meshes from the shared 6 axis + 4 table cameras, with masks.

Fusion360 (maksimko123/fusion360_test_mesh, 1725 STL meshes) ships as meshes, not CAD json, so this
is the mesh counterpart of render_views.py. Same layout and conventions, but a numpy z-buffer
rasteriser instead of pyrender (no EGL/OpenGL needed; works on Windows ARM).

usage: python render_fusion360.py split            # writes splits/fusion360_{train,test}.txt
       python render_fusion360.py render <train|test> [limit] [--jobs N]

reads   data/raw/fusion360_test_mesh/<part>.stl            (git-ignored)
writes  data/renders/fusion360/<split>/<part>/{rgb,mask}/<view>.png and depth.npz
        data/renders/fusion360/<split>/manifest.json
        data/meshes_hidden/fusion360/<split>/<part>.stl and <part>_{axis,table}_posed.stl (git-ignored)

Poses are seeded from SEED + part name, as in render_views.py:
  axis  views: uniformly random 3D rotation.
  table views: a physically stable resting pose, then a random spin about +Z.
Frames: x_render = R @ (scale * (x_canonical - centre)), centre = bbox centre,
scale = 1 / bounding-sphere radius about that centre.
"""
import argparse
import json
import random
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import trimesh
import trimesh.transformations as tf
from PIL import Image

import cameras

SEED = 2529
HERE = Path(__file__).parent
SRC = HERE / "raw" / "fusion360_test_mesh"
TEST_FRACTION = 0.2


def all_parts():
    """All 1725 part names, from the Hugging Face listing saved next to the meshes."""
    listing = HERE / "splits" / "fusion360_all.txt"
    if listing.exists():
        return [l.strip() for l in listing.read_text().split() if l.strip()]
    return sorted(p.stem for p in SRC.glob("*.stl"))


def make_split():
    names = sorted(all_parts())
    rng = random.Random(SEED)
    rng.shuffle(names)
    n_test = round(len(names) * TEST_FRACTION)
    test, train = sorted(names[:n_test]), sorted(names[n_test:])
    (HERE / "splits" / "fusion360_train.txt").write_text("\n".join(train) + "\n")
    (HERE / "splits" / "fusion360_test.txt").write_text("\n".join(test) + "\n")
    (HERE / "splits" / "fusion360_meta.json").write_text(json.dumps(
        {"seed": SEED, "source": "maksimko123/fusion360_test_mesh (Fusion360 reconstruction test split)",
         "n_source": len(names), "n_train": len(train), "n_test": len(test)}, indent=2))
    print(f"train {len(train)}, test {len(test)}")


# ------------------------------------------------------------------ geometry
def normalise(mesh):
    lo, hi = mesh.bounds
    centre = (lo + hi) / 2
    m = mesh.copy()
    m.apply_translation(-centre)
    r = np.linalg.norm(m.vertices, axis=1).max()
    m.apply_scale(cameras.RADIUS / r)
    return m, centre, r


def pose_rotations(mesh_n, rng):
    r_axis = tf.random_rotation_matrix(rng.random(3))[:3, :3]
    info = {}
    try:
        transforms, probs = trimesh.poses.compute_stable_poses(mesh_n, n_samples=1)
        probs = np.asarray(probs, float)
        k = rng.choice(len(transforms), p=probs / probs.sum())
        r_stable = np.asarray(transforms[k])[:3, :3]
        info["stable_pose_index"] = int(k)
        info["stable_pose_prob"] = float(probs[k] / probs.sum())
    except Exception as e:
        r_stable = np.eye(3)
        info["stable_pose_fallback"] = f"{type(e).__name__}: {e}"
    yaw = rng.uniform(0, 2 * np.pi)
    r_table = tf.rotation_matrix(yaw, [0, 0, 1])[:3, :3] @ r_stable
    info["yaw_deg"] = float(np.degrees(yaw))
    info["table_plane_z"] = float((mesh_n.vertices @ r_table.T)[:, 2].min())
    return r_axis, r_table, info


def posed(mesh_n, rot):
    m = mesh_n.copy()
    m.apply_transform(np.block([[rot, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]))
    return m


# ------------------------------------------------------------------ rasteriser
COLOR = np.array([0.72, 0.74, 0.78])


def rasterise(mesh, pose, size=cameras.IMG, yfov_deg=cameras.YFOV_DEG, znear=0.05, zfar=20.0):
    """-> rgb (size,size,3 uint8, background white), depth (float32, z along view axis, 0 = background)."""
    f = 0.5 * size / np.tan(np.radians(yfov_deg) / 2)
    R, t = pose[:3, :3], pose[:3, 3]
    cam = (mesh.vertices - t) @ R                      # OpenGL camera frame, looks down -z
    z = -cam[:, 2]
    zc = np.maximum(z, 1e-9)
    px = f * cam[:, 0] / zc + size / 2
    py = size / 2 - f * cam[:, 1] / zc
    view = R[:, 2]
    normals = mesh.face_normals
    zbuf = np.full((size, size), np.inf)
    shade = np.zeros((size, size))
    for fi, tri in enumerate(mesh.faces):
        zs = z[tri]
        if (zs <= znear).any():
            continue
        xs, ys = px[tri], py[tri]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), size - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), size - 1)
        if x0 > x1 or y0 > y1:
            continue
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        dep = 1.0 / np.maximum(w0 / zs[0] + w1 / zs[1] + w2 / zs[2], 1e-12)  # perspective-correct
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (dep < sub) & (dep < zfar)
        if not upd.any():
            continue
        sub[upd] = dep[upd]
        shade[y0:y1 + 1, x0:x1 + 1][upd] = 0.3 + 0.7 * abs(float(normals[fi] @ view))
    mask = np.isfinite(zbuf)
    rgb = np.full((size, size, 3), 255, np.uint8)
    rgb[mask] = (COLOR[None] * shade[mask][:, None] * 255).astype(np.uint8)
    return rgb, np.where(mask, zbuf, 0.0).astype(np.float32)


# ------------------------------------------------------------------ one part
def render_part(args):
    name, split = args
    try:
        mesh = trimesh.load_mesh(SRC / f"{name}.stl")
        mesh_root = HERE / "meshes_hidden" / "fusion360" / split
        out = HERE / "renders" / "fusion360" / split / name
        mesh_root.mkdir(parents=True, exist_ok=True)
        (out / "rgb").mkdir(parents=True, exist_ok=True)
        (out / "mask").mkdir(parents=True, exist_ok=True)
        mesh.export(mesh_root / f"{name}.stl")
        mesh_n, centre, r = normalise(mesh)
        rng = np.random.default_rng([SEED, zlib.crc32(name.encode())])
        r_axis, r_table, tinfo = pose_rotations(mesh_n, rng)
        views = cameras.views()
        depths = {}
        for g, rot in (("axis", r_axis), ("table", r_table)):
            mp = posed(mesh_n, rot)
            mp.export(mesh_root / f"{name}_{g}_posed.stl")
            for vname, v in views.items():
                if v["group"] != g:
                    continue
                rgb, depth = rasterise(mp, v["pose"])
                mask = depth > 0
                Image.fromarray(rgb).save(out / "rgb" / f"{vname}.png")
                Image.fromarray((mask * 255).astype(np.uint8)).save(out / "mask" / f"{vname}.png")
                depths[vname] = depth.astype(np.float16)
        np.savez_compressed(out / "depth.npz", **depths)
        return name, {"part": name, "centre": centre.tolist(), "scale": 1.0 / r,
                      "R_axis": r_axis.round(9).tolist(), "R_table": r_table.round(9).tolist(),
                      "table": tinfo, "n_triangles": int(len(mesh.faces)),
                      "watertight": bool(mesh.is_watertight)}, None
    except Exception as e:
        return name, None, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["split", "render"])
    ap.add_argument("split", nargs="?", choices=["train", "test"])
    ap.add_argument("limit", nargs="?", type=int)
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    cameras.write_json(HERE / "cameras.json")
    if a.mode == "split":
        return make_split()
    names = [l.strip() for l in open(HERE / "splits" / f"fusion360_{a.split}.txt") if l.strip()][:a.limit]
    todo = [n for n in names if (SRC / f"{n}.stl").exists()]
    if len(todo) < len(names):
        print(f"warning: {len(names) - len(todo)} meshes not downloaded yet, skipping them")
    out_root = HERE / "renders" / "fusion360" / a.split
    out_root.mkdir(parents=True, exist_ok=True)
    mpath = out_root / "manifest.json"
    prev = json.loads(mpath.read_text()) if mpath.exists() else {"rendered": {}, "failed": {}}
    todo = [n for n in todo if n not in prev["rendered"]]
    with ProcessPoolExecutor(a.jobs) as ex:
        for i, (name, rec, err) in enumerate(ex.map(render_part, [(n, a.split) for n in todo]), 1):
            if err:
                prev["failed"][name] = err
            else:
                prev["rendered"][name] = rec
                prev["failed"].pop(name, None)
            if i % 25 == 0:
                print(f"{i}/{len(todo)}", flush=True)
                mpath.write_text(json.dumps(prev))
    prev.update(split=a.split, seed=SEED)
    mpath.write_text(json.dumps(prev, indent=1))
    print(f"{a.split}: rendered {len(prev['rendered'])}, failed {len(prev['failed'])}")


if __name__ == "__main__":
    main()
