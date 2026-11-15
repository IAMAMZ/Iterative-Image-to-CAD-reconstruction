"""Render CadQuery shapes offscreen with pyrender.

    from cq_render import render_shape
    rgb, depth, mask = render_shape(cq.Workplane().box(1, 2, 3), azim=45, elev=30)

Run as a script for a demo:  uv run python cq_render.py --out out/demo
"""
import os
import sys

if sys.platform.startswith("linux"):
    os.environ.setdefault("PYOPENGL_PLATFORM", "egl")  # headless rendering (macOS uses pyrender's default backend)

import argparse
import math
from pathlib import Path

import cadquery as cq
import numpy as np
import pyrender
import trimesh
from PIL import Image


def to_trimesh(shape, tolerance=0.01, angular_tolerance=0.1):
    """Tessellate a cq.Workplane / cq.Shape into a trimesh.Trimesh."""
    if isinstance(shape, cq.Workplane):
        vals = [v for v in shape.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValueError("Workplane contains no shapes")
        shape = vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    verts, tris = shape.tessellate(tolerance, angular_tolerance)
    if not tris:
        raise ValueError("tessellation produced no triangles")
    v = np.array([p.toTuple() for p in verts], dtype=np.float64)
    f = np.array(tris, dtype=np.int64)
    return trimesh.Trimesh(v, f, process=True)


def look_at(eye, target, up=(0.0, 0.0, 1.0)):
    """Camera-to-world pose (OpenGL convention: camera looks down -z)."""
    eye, target, up = map(np.asarray, (eye, target, up))
    z = eye - target
    z = z / np.linalg.norm(z)
    if abs(np.dot(z, up / np.linalg.norm(up))) > 0.999:  # looking straight up/down
        up = np.array([0.0, 1.0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    pose = np.eye(4)
    pose[:3, 0], pose[:3, 1], pose[:3, 2], pose[:3, 3] = x, y, z, eye
    return pose


def camera_pose(mesh, azim=45.0, elev=30.0, yfov=math.radians(40), margin=1.15):
    """Pose on a sphere around the mesh that fits its bounding sphere in view."""
    center = mesh.bounding_box.centroid
    radius = np.linalg.norm(mesh.extents) / 2.0
    dist = margin * radius / math.sin(yfov / 2.0)
    a, e = math.radians(azim), math.radians(elev)
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    return look_at(center + dist * d, center), dist, radius


class CQRenderer:
    """Reusable offscreen renderer (creating the GL context is the slow part)."""

    def __init__(self, width=512, height=512, yfov=math.radians(40)):
        self.width, self.height, self.yfov = width, height, yfov
        self.renderer = pyrender.OffscreenRenderer(width, height)

    def render(self, shape, azim=45.0, elev=30.0, color=(0.55, 0.62, 0.72),
               bg=(0.92, 0.92, 0.92), tolerance=0.01):
        """-> rgb (H,W,3 uint8), depth (H,W float32, 0 = background), mask (H,W bool)."""
        mesh = shape if isinstance(shape, trimesh.Trimesh) else to_trimesh(shape, tolerance)
        pose, dist, radius = camera_pose(mesh, azim, elev, self.yfov)
        return self.render_pose(mesh, pose, znear=max(dist - 2 * radius, 1e-3),
                                zfar=dist + 2 * radius, color=color, bg=bg)

    def render_pose(self, mesh, pose, znear, zfar, yfov=None,
                    color=(0.55, 0.62, 0.72), bg=(0.92, 0.92, 0.92)):
        """Render a trimesh from an explicit camera-to-world pose (OpenGL convention)."""
        pose = np.asarray(pose, dtype=np.float64)
        scene = pyrender.Scene(bg_color=(*bg, 1.0), ambient_light=(0.3, 0.3, 0.3))
        mat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=(*color, 1.0), metallicFactor=0.0, roughnessFactor=0.7)
        scene.add(pyrender.Mesh.from_trimesh(mesh, material=mat, smooth=False))

        cam = pyrender.PerspectiveCamera(
            yfov=yfov or self.yfov, aspectRatio=self.width / self.height,
            znear=znear, zfar=zfar)
        scene.add(cam, pose=pose)
        scene.add(pyrender.DirectionalLight(intensity=1.2), pose=pose)  # headlight
        dist = 0.5 * (znear + zfar)
        target = pose[:3, 3] - pose[:3, 2] * dist  # point in front of the camera
        key = look_at(pose[:3, 3] + pose[:3, 0] * dist, target)
        scene.add(pyrender.DirectionalLight(intensity=1.0), pose=key)  # side fill

        rgb, depth = self.renderer.render(scene)
        return rgb, depth, depth > 0

    def close(self):
        self.renderer.delete()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def render_shape(shape, width=512, height=512, **kw):
    """One-shot convenience wrapper around CQRenderer."""
    with CQRenderer(width, height) as r:
        return r.render(shape, **kw)


def demo_part():
    """A small bracket-like part exercising fillets, holes and a boolean cut."""
    return (
        cq.Workplane("XY").box(40, 30, 8)
        .edges("|Z").fillet(4)
        .faces(">Z").workplane().rarray(25, 15, 2, 2).hole(4)
        .faces(">Z").workplane().center(0, 0).rect(12, 30).cutBlind(-4)
        .faces(">Z").workplane().center(14, 0).circle(4).extrude(10)
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="out/demo", help="output directory")
    ap.add_argument("--size", type=int, default=512)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    part = demo_part()
    cq.exporters.export(part, str(out / "demo.step"))
    views = {"iso": (45, 30), "front": (-90, 0), "right": (0, 0), "top": (-90, 90)}
    with CQRenderer(args.size, args.size) as r:
        mesh = to_trimesh(part)  # tessellate once, reuse for every view
        for name, (az, el) in views.items():
            rgb, depth, mask = r.render(mesh, azim=az, elev=el)
            Image.fromarray(rgb).save(out / f"{name}.png")
            Image.fromarray((mask * 255).astype(np.uint8)).save(out / f"{name}_mask.png")
    print(f"wrote {len(views)} views + demo.step to {out}/")


if __name__ == "__main__":
    main()
