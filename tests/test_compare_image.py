"""Image-mode checker: target is only a picture (no 3D model), camera known or unknown."""
import math

import numpy as np
import pytest
import trimesh
from PIL import Image

from compare_image import align, compare_image, iou, target_mask, warp
from cq_render import CQRenderer
from generate_solid import generate
from rig import _pose, load_rig, normalize

L_PART = ("import cadquery as cq\n"   # asymmetric, so its pose is well defined
          "result = cq.Workplane().box(40, 20, 8).faces('>Z').workplane()"
          ".center(12, 0).rect(16, 20).extrude(20).faces('>Z').workplane().hole(5)\n")
BOX = "import cadquery as cq\nresult = cq.Workplane().box(30, 30, 30)\n"


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    tmp, rig = tmp_path_factory.mktemp("ci"), load_rig()
    for name, src in (("l_part", L_PART), ("box", BOX)):
        (tmp / f"{name}.py").write_text(src)
        generate(tmp / f"{name}.py", tmp / name, rig)
    # the "photo": the L part from an off-rig pose, smaller and off-centre in the frame
    mesh, _, _ = normalize(trimesh.load(tmp / "l_part" / "solid.stl", force="mesh"))
    with CQRenderer(256, 256) as r:
        rgb, _, _ = r.render_pose(mesh, _pose(110, 25), rig["znear"], rig["zfar"],
                                  math.radians(rig["yfov_deg"]))
    photo = Image.new("RGB", (256, 256), tuple(int(v) for v in rgb[0, 0]))
    photo.paste(Image.fromarray(rgb).resize((180, 180)), (60, 10))
    photo.save(tmp / "photo.png")
    return tmp


def test_target_mask_from_plain_background_alpha_and_mask():
    rgb = np.full((20, 20, 3), 235, np.uint8)
    rgb[5:15, 5:10] = (140, 150, 170)
    want = np.zeros((20, 20), bool)
    want[5:15, 5:10] = True
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        Image.fromarray(rgb).save(f"{d}/a.png")
        Image.fromarray(want.astype(np.uint8) * 255).save(f"{d}/m.png")
        Image.fromarray(np.dstack([rgb, want.astype(np.uint8) * 255])).save(f"{d}/t.png")
        for f in ("a.png", "m.png", "t.png"):
            assert (target_mask(f"{d}/{f}")[0] == want).all(), f


def test_alignment_undoes_shift_and_scale():
    a = np.zeros((100, 100), bool)
    a[20:40, 30:70] = True                              # 20 x 40 rectangle
    b = np.zeros((100, 100), bool)
    b[60:70, 10:30] = True                              # same shape, half size, elsewhere
    al = align(a, b)
    assert al["scale"] == pytest.approx(2, rel=0.01)
    assert iou(a, warp(b, al["scale"], al["src"], al["dst"], a.shape)) > 0.9


def test_search_finds_pose_of_right_part(setup):
    r = compare_image(setup / "photo.png", setup / "l_part", setup / "out_right")
    assert r["iou"] > 0.97
    c = r["camera"]
    assert abs((c["azim_deg"] - 110 + 180) % 360 - 180) < 5 and abs(c["elev_deg"] - 25) < 5
    for f in ("overlay.png", "summary.png", "report.json"):
        assert (setup / "out_right" / f).exists()


def test_wrong_part_scores_lower(setup):
    right = compare_image(setup / "photo.png", setup / "l_part", setup / "o1")
    wrong = compare_image(setup / "photo.png", setup / "box", setup / "o2")
    assert wrong["iou"] < right["iou"] - 0.1


def test_known_camera_mode(setup):
    """A rig render scored with its own camera is near perfect; with another camera it is not."""
    img = setup / "l_part" / "iso_fr.png"
    good = compare_image(img, setup / "l_part", setup / "o3", camera="iso_fr")
    bad = compare_image(img, setup / "l_part", setup / "o4", camera="front")
    assert good["iou"] > 0.99 and bad["iou"] < 0.9
    with pytest.raises(ValueError, match="unknown camera"):
        compare_image(img, setup / "l_part", setup / "o5", camera="nope")
