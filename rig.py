"""Fixed camera rig shared by every render, saved to / loaded from rig.json.

Convention
  * world is Z-up; the part is first normalised: its bounding-box centre is moved
    to the origin and it is scaled so its bounding sphere has radius 1
    (see `normalize`). Every camera then looks at the origin from DISTANCE.
  * poses are 4x4 camera-to-world matrices in the OpenGL convention
    (camera looks down its -z axis, +y is image up) -- what pyrender expects.
  * K is the pinhole intrinsics in pixels for the OpenCV convention
    (x right, y down); convert a pose to OpenCV with pose @ diag(1, -1, -1, 1).
  * depth maps are distance along the camera's viewing axis, in normalised units
    (multiply by 1/scale from info.json for original part units); 0 = background.

Regenerate the file with:  uv run python rig.py
"""
import json
import math
from pathlib import Path

import numpy as np

from cq_render import look_at

RIG_PATH = Path(__file__).with_name("rig.json")

WIDTH = HEIGHT = 512
YFOV_DEG = 40.0
DISTANCE = 3.5            # unit sphere fills ~85% of the frame height
ZNEAR, ZFAR = 1.0, 6.0    # brackets the unit sphere (2.5 .. 4.5) with slack

# name -> (azimuth deg, elevation deg). azimuth 0 = +X, 90 = +Y; elevation from the XY plane.
# "front" looks from -Y toward +Y, so +X is to the right of the image.
VIEWS = {
    "front":     (-90.0,   0.0),
    "back":      ( 90.0,   0.0),
    "right":     (  0.0,   0.0),
    "left":      (180.0,   0.0),
    "top":       (-90.0,  90.0),
    "bottom":    (-90.0, -90.0),
    "iso_fr":    (-45.0,  30.0),   # front-right, from above
    "iso_bl":    (135.0,  30.0),   # back-left, from above
}


def _pose(azim, elev, dist=DISTANCE):
    a, e = math.radians(azim), math.radians(elev)
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    d[np.abs(d) < 1e-12] = 0.0
    if abs(d[2]) > 0.999:
        # straight up/down: keep image-up aligned with the azimuth direction so that
        # "top" has +Y up (front edge at the bottom of the image), like a drafting top view.
        up = -np.array([math.cos(a), math.sin(a), 0.0]) * np.sign(d[2])
    else:
        up = (0.0, 0.0, 1.0)
    return look_at(dist * d, np.zeros(3), up)


def build_rig():
    fy = 0.5 * HEIGHT / math.tan(math.radians(YFOV_DEG) / 2)
    K = [[fy, 0.0, WIDTH / 2], [0.0, fy, HEIGHT / 2], [0.0, 0.0, 1.0]]
    cams = []
    for name, (az, el) in VIEWS.items():
        pose = _pose(az, el)
        pose[np.abs(pose) < 1e-12] = 0.0
        cams.append({"name": name, "azim_deg": az, "elev_deg": el,
                     "pose_c2w": pose.round(12).tolist()})
    return {
        "convention": "Z-up world; part normalised to unit bounding sphere at origin; "
                      "pose_c2w is OpenGL camera-to-world (camera looks down -z); "
                      "K is OpenCV pixel intrinsics",
        "width": WIDTH, "height": HEIGHT, "yfov_deg": YFOV_DEG,
        "distance": DISTANCE, "znear": ZNEAR, "zfar": ZFAR,
        "K": K, "cameras": cams,
    }


def save_rig(path=RIG_PATH):
    Path(path).write_text(json.dumps(build_rig(), indent=2) + "\n")


def load_rig(path=RIG_PATH):
    return json.loads(Path(path).read_text())


def normalize(mesh):
    """Return (normalised copy, center, scale) with  x_norm = (x - center) * scale."""
    center = mesh.bounding_box.centroid
    scale = 1.0 / (np.linalg.norm(mesh.extents) / 2.0)
    m = mesh.copy()
    m.apply_translation(-center)
    m.apply_scale(scale)
    return m, center, scale


def render_rig(renderer, mesh, rig):
    """Render a *normalised* mesh from every rig camera -> {name: (rgb, depth, mask)}."""
    yfov = math.radians(rig["yfov_deg"])
    return {c["name"]: renderer.render_pose(mesh, c["pose_c2w"], rig["znear"], rig["zfar"], yfov)
            for c in rig["cameras"]}


if __name__ == "__main__":
    save_rig()
    print(f"wrote {len(VIEWS)} cameras to {RIG_PATH}")
