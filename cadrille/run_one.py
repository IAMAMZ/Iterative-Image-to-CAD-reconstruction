"""Run cadrille (img mode) on ONE mesh, CPU-only, no open3d / flash-attn / pytorch3d.

Reproduces dataset.CadRecodeDataset.get_img: mesh normalised to the unit cube, 4 views
(fronts [1,1,1] [-1,-1,-1] [-1,1,-1] [1,-1,1], dist 0.9, 60deg fov, 500px -> 128px),
tiled 2x2 with a 3px black border, fed to the model as a 1-frame "video".
Open3D is replaced by a small numpy z-buffer rasteriser (same camera maths, simple headlight shading).

  python run_one.py path/to/mesh.stl --out work_dirs/one
"""
import argparse
import os
import time

import numpy as np
import torch
import trimesh
from PIL import Image, ImageOps
from transformers import AutoProcessor

from cadrille import Cadrille, collate

FRONTS = [[1, 1, 1], [-1, -1, -1], [-1, 1, -1], [1, -1, 1]]
YELLOW = np.array([255, 255, 136]) / 255.0


def normalize_unit_cube(mesh):
    """Centre bbox at (0.5,0.5,0.5), longest side = 1 (the layout the test meshes use)."""
    mesh = mesh.copy()
    lo, hi = mesh.bounds
    mesh.apply_translation(-(lo + hi) / 2)
    mesh.apply_scale(1.0 / (hi - lo).max())
    mesh.apply_translation([0.5, 0.5, 0.5])
    return mesh


def render_view(mesh, front, distance=0.9, size=500, fov_deg=60.0):
    lookat = np.array([0.5, 0.5, 0.5])
    front = np.array(front, float)
    up = np.array([0.0, 1.0, 0.0])
    eye = lookat - distance * front            # open3d: eye = lookat + front * camera_distance(-0.9)
    right = np.cross(up, front); right /= np.linalg.norm(right)
    true_up = np.cross(front, right)           # rows of the open3d extrinsic: right, true_up, front
    R = np.stack([right, true_up, front])      # (camera y = true_up, i.e. image-down, as in open3d)
    cam = (mesh.vertices - eye) @ R.T
    f = (size / 2) / np.tan(np.radians(fov_deg) / 2)
    z = cam[:, 2]
    px = f * cam[:, 0] / z + size / 2
    py = f * cam[:, 1] / z + size / 2

    img = np.ones((size, size, 3))
    zbuf = np.full((size, size), np.inf)
    normals = mesh.face_normals
    view_dirs = front / np.linalg.norm(front)
    for fi, tri in enumerate(mesh.faces):
        zs = z[tri]
        if (zs <= 1e-6).any():
            continue
        xs, ys = px[tri], py[tri]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), size - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), size - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        depth = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (depth < sub)
        if not upd.any():
            continue
        sub[upd] = depth[upd]
        shade = 0.35 + 0.65 * abs(float(normals[fi] @ view_dirs))
        img[y0:y1 + 1, x0:x1 + 1][upd] = YELLOW * shade
    return Image.fromarray((img * 255).astype(np.uint8))


def make_grid_soft(mesh, img_size=128):
    views = [render_view(mesh, f).resize((img_size, img_size), Image.LANCZOS) for f in FRONTS]
    views = [ImageOps.expand(v, border=3, fill='black') for v in views]
    a = [np.array(v) for v in views]
    return Image.fromarray(np.vstack((np.hstack(a[:2]), np.hstack(a[2:]))))


def o3d_view(o3d_mesh, front, distance=-0.9, size=500, img_size=128):
    """Exact copy of dataset.mesh_to_image (open3d offscreen)."""
    import open3d
    import skimage.transform
    vis = open3d.visualization.Visualizer()
    vis.create_window(width=size, height=size, visible=False)
    vis.add_geometry(o3d_mesh)
    lookat = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    fa = np.array(front, dtype=np.float32)
    up = np.array([0, 1, 0], dtype=np.float32)
    eye = lookat + fa * distance
    right = np.cross(up, fa)
    right /= np.linalg.norm(right)
    true_up = np.cross(fa, right)
    R = np.column_stack((right, true_up, fa)).T
    ext = np.eye(4)
    ext[:3, :3] = R
    ext[:3, 3] = -R @ eye
    vc = vis.get_view_control()
    cp = vc.convert_to_pinhole_camera_parameters()
    cp.extrinsic = ext
    vc.convert_from_pinhole_camera_parameters(cp)
    vis.poll_events()
    vis.update_renderer()
    im = np.asarray(vis.capture_screen_float_buffer(do_render=True))
    vis.destroy_window()
    assert im.shape[:2] == (size, size), im.shape
    im = (im * 255).astype(np.uint8)
    im = skimage.transform.resize(im, (img_size, img_size), order=2, anti_aliasing=True,
                                  preserve_range=True).astype(np.uint8)
    return Image.fromarray(im)


def make_grid(mesh, img_size=128):
    """Same 2x2 mosaic as dataset.CadRecodeDataset.get_img, rendered with open3d."""
    import open3d
    m = open3d.geometry.TriangleMesh()
    m.vertices = open3d.utility.Vector3dVector(np.asarray(mesh.vertices))
    m.triangles = open3d.utility.Vector3iVector(np.asarray(mesh.faces))
    m.paint_uniform_color(YELLOW)
    m.compute_vertex_normals()
    views = [ImageOps.expand(o3d_view(m, f, img_size=img_size), border=3, fill='black') for f in FRONTS]
    a = [np.array(v) for v in views]
    return Image.fromarray(np.vstack((np.hstack(a[:2]), np.hstack(a[2:]))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mesh')
    ap.add_argument('--checkpoint', default='checkpoints/cadrille')
    ap.add_argument('--out', default='work_dirs/one')
    ap.add_argument('--max-new-tokens', type=int, default=768)
    ap.add_argument('--dtype', default='bfloat16', choices=['bfloat16', 'float32'])
    ap.add_argument('--render-only', action='store_true')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.mesh))[0]

    mesh = normalize_unit_cube(trimesh.load(args.mesh, force='mesh'))
    t = time.time()
    grid = make_grid(mesh)
    grid.save(os.path.join(args.out, f'{stem}_input.png'))
    print(f'rendered input {grid.size} in {time.time() - t:.1f}s')
    if args.render_only:
        return

    dtype = getattr(torch, args.dtype)
    model = Cadrille.from_pretrained(args.checkpoint, torch_dtype=dtype,
                                     attn_implementation='sdpa', device_map='cpu')
    model.eval()
    processor = AutoProcessor.from_pretrained(
        'Qwen/Qwen2-VL-2B-Instruct', min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28,
        padding_side='left')

    batch = collate([{'video': [grid], 'description': 'Generate cadquery code', 'file_name': stem}],
                    processor=processor, n_points=256, eval=True)
    t = time.time()
    with torch.no_grad():
        ids = model.generate(
            input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
            point_clouds=batch['point_clouds'], is_pc=batch['is_pc'], is_img=batch['is_img'],
            pixel_values_videos=batch['pixel_values_videos'].to(dtype),
            video_grid_thw=batch['video_grid_thw'],
            max_new_tokens=args.max_new_tokens)
    out = processor.batch_decode([ids[0][len(batch['input_ids'][0]):]], skip_special_tokens=True,
                                 clean_up_tokenization_spaces=False)[0]
    print(f'generated in {time.time() - t:.0f}s')
    path = os.path.join(args.out, f'{stem}.py')
    with open(path, 'w') as f:
        f.write(out)
    print(f'--- {path} ---\n{out}')


if __name__ == '__main__':
    main()
