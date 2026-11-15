"""generate_solid.py with a numpy software rasteriser instead of pyrender/EGL.

For machines with no working OpenGL (e.g. Windows on ARM). Same camera rig, same
outputs (rgb / depth / mask), so compare.py works on the results unchanged.

    python soft_generate.py prog.py --out out/x [--like out/target]
"""
import sys
import types

import numpy as np

# cq_render imports pyrender at module level, which needs EGL; stub it, we never call it.
sys.modules.setdefault("pyrender", types.ModuleType("pyrender"))

import cq_render  # noqa: E402


class SoftRenderer:
    def __init__(self, width=512, height=512, yfov=None):
        self.width, self.height = width, height
        self.yfov = yfov

    def render(self, *a, **k):
        raise NotImplementedError

    def render_pose(self, mesh, pose, znear, zfar, yfov=None, color=(0.55, 0.62, 0.72),
                    bg=(0.92, 0.92, 0.92)):
        W, H = self.width, self.height
        pose = np.asarray(pose, float)
        f = 0.5 * H / np.tan((yfov or self.yfov) / 2)
        R, t = pose[:3, :3], pose[:3, 3]
        cam = (mesh.vertices - t) @ R               # camera coords, OpenGL: looks down -z
        z = -cam[:, 2]                              # distance along the viewing axis
        px = f * cam[:, 0] / np.maximum(z, 1e-9) + W / 2
        py = H / 2 - f * cam[:, 1] / np.maximum(z, 1e-9)
        depth_buf = np.full((H, W), np.inf)
        shade = np.zeros((H, W))
        view = R[:, 2]                              # camera +z axis in world (towards viewer)
        normals = mesh.face_normals
        for fi, tri in enumerate(mesh.faces):
            zs = z[tri]
            if (zs <= znear).any():
                continue
            xs, ys = px[tri], py[tri]
            x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), W - 1)
            y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), H - 1)
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
            # perspective-correct depth: 1/z is linear in screen space
            inv = w0 / zs[0] + w1 / zs[1] + w2 / zs[2]
            dep = 1.0 / np.maximum(inv, 1e-12)
            sub = depth_buf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (dep < sub) & (dep < zfar)
            if not upd.any():
                continue
            sub[upd] = dep[upd]
            shade[y0:y1 + 1, x0:x1 + 1][upd] = 0.3 + 0.7 * abs(float(normals[fi] @ view))
        mask = np.isfinite(depth_buf)
        depth = np.where(mask, depth_buf, 0.0).astype(np.float32)
        img = np.empty((H, W, 3))
        img[:] = bg
        img[mask] = np.asarray(color)[None] * shade[mask][:, None]
        return (img * 255).astype(np.uint8), depth, mask

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


cq_render.CQRenderer = SoftRenderer

import generate_solid  # noqa: E402  (imports CQRenderer from cq_render -> our class)

if __name__ == "__main__":
    generate_solid.main()
