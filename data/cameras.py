"""Shared camera definitions. Every part is normalised (centred on its bounding-box
centre, scaled so its bounding sphere has radius 1, +Z up) and then viewed with the
SAME intrinsics and poses, so a single cameras.json describes all renders.

Set A "axis" (6):  top, bottom, front, back, left, right  (on the coordinate axes)
Set B "table" (4): top_left, top_right, top_front, top_back (45 deg above the table)

Conventions: world +Z is up; "front" camera sits on -Y looking toward +Y; "right" camera
sits on +X; "left" on -X; "back" on +Y. Camera pose = OpenGL camera-to-world
(camera looks down its -Z axis, +Y up in the image).
"""
import json
import math

import numpy as np

IMG = 512
YFOV_DEG = 40.0
RADIUS = 1.0  # normalised bounding-sphere radius
DIST = 1.15 * RADIUS / math.sin(math.radians(YFOV_DEG / 2))  # sphere fits with 15% margin
ELEV_DEG = 45.0

_AXIS = {  # name -> (camera position direction, image-up vector)
    "top": ((0, 0, 1), (0, 1, 0)),
    "bottom": ((0, 0, -1), (0, -1, 0)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "back": ((0, 1, 0), (0, 0, 1)),
    "left": ((-1, 0, 0), (0, 0, 1)),
    "right": ((1, 0, 0), (0, 0, 1)),
}


def _table(azim_dir):
    e = math.radians(ELEV_DEG)
    h = np.array(azim_dir, float)
    return (h[0] * math.cos(e), h[1] * math.cos(e), math.sin(e)), (0, 0, 1)


_TABLE = {
    "top_left": _table((-1, 0, 0)),
    "top_right": _table((1, 0, 0)),
    "top_front": _table((0, -1, 0)),
    "top_back": _table((0, 1, 0)),
}


def look_at(eye, up, target=(0, 0, 0)):
    eye, up, target = (np.array(v, float) for v in (eye, up, target))
    z = eye - target
    z /= np.linalg.norm(z)
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, eye
    return m


def views():
    out = {}
    for group, table in (("axis", _AXIS), ("table", _TABLE)):
        for name, (direction, up) in table.items():
            d = np.array(direction, float)
            d /= np.linalg.norm(d)
            out[name] = {"group": group, "pose": look_at(d * DIST, up)}
    return out


def write_json(path):
    f = 0.5 * IMG / math.tan(math.radians(YFOV_DEG / 2))
    doc = {
        "image_size": [IMG, IMG],
        "yfov_deg": YFOV_DEG,
        "intrinsics": {"fx": f, "fy": f, "cx": IMG / 2, "cy": IMG / 2},
        "normalisation": "centre = bbox centre, scale = 1 / bounding-sphere radius, +Z up",
        "pose_convention": "OpenGL camera-to-world 4x4 (camera looks along -Z, +Y up)",
        "views": {k: {"group": v["group"], "pose": v["pose"].round(6).tolist()}
                  for k, v in views().items()},
    }
    json.dump(doc, open(path, "w"), indent=2)
