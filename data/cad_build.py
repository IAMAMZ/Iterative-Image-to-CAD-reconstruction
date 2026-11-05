"""Rebuild a solid from a raw DeepCAD cad_json file with CadQuery.

Follows the conventions of the reference code (cadlib/extrude.py, visualize.py):
  * curve points are local 2D sketch coordinates (x, y); z is ignored
  * arcs: midpoint = center + R(mean(start_angle, end_angle)) @ reference_vector * radius
  * extent: OneSide = +extent_one along sketch normal; Symmetric = +/- extent_one;
    TwoSides = +extent_one along normal and extent_two against it. Taper is ignored.
  * the first extrude is always a new body; later ones fuse / cut / intersect
Differences: we use the sketch frame stored in the json directly (the reference
code re-derives it through a polar parameterisation that can flip frames) and
use the is_outer flag to choose the outer loop.
"""
import json
import math

import cadquery as cq


def _v(d):
    return cq.Vector(d["x"], d["y"], d["z"])


class BuildError(Exception):
    pass


def _curve(c):
    """-> (kind, start(2), end(2), extra) in local sketch coords."""
    t = c["type"]
    if t == "Line3D":
        s = (c["start_point"]["x"], c["start_point"]["y"])
        e = (c["end_point"]["x"], c["end_point"]["y"])
        return ("line", s, e, None)
    if t == "Arc3D":
        s = (c["start_point"]["x"], c["start_point"]["y"])
        e = (c["end_point"]["x"], c["end_point"]["y"])
        ctr = (c["center_point"]["x"], c["center_point"]["y"])
        ref = (c["reference_vector"]["x"], c["reference_vector"]["y"])
        a = (c["start_angle"] + c["end_angle"]) / 2.0
        ca, sa = math.cos(a), math.sin(a)
        m = (ctr[0] + (ca * ref[0] - sa * ref[1]) * c["radius"],
             ctr[1] + (sa * ref[0] + ca * ref[1]) * c["radius"])
        return ("arc", s, e, m)
    if t == "Circle3D":
        return ("circle", (c["center_point"]["x"], c["center_point"]["y"]), None, c["radius"])
    raise BuildError(f"unsupported curve type {t}")


def _loop_wire(loop, to_world):
    curves = [_curve(c) for c in loop["profile_curves"]]
    if len(curves) == 1 and curves[0][0] == "circle":
        _, ctr, _, r = curves[0]
        return cq.Wire.makeCircle(abs(r), to_world(ctr), _NORMAL[0])
    if any(c[0] == "circle" for c in curves):
        raise BuildError("circle mixed with other curves")
    pts = [p for c in curves for p in (c[1], c[2])]
    size = max(max(p[0] for p in pts) - min(p[0] for p in pts),
               max(p[1] for p in pts) - min(p[1] for p in pts), 1e-9)
    tol = 1e-3 * size
    # drop degenerate (near zero-length) lines
    curves = [c for c in curves
              if not (c[0] == "line" and math.hypot(c[1][0] - c[2][0], c[1][1] - c[2][1]) <= tol)]
    if not curves:
        raise BuildError("empty loop")

    def close(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol

    remaining = curves[1:]
    chain = [curves[0]]
    while remaining:
        end = chain[-1][2]
        for i, c in enumerate(remaining):
            if close(c[1], end):
                chain.append(c)
            elif close(c[2], end):
                chain.append((c[0], c[2], c[1], c[3]))
            else:
                continue
            remaining.pop(i)
            break
        else:
            raise BuildError("open loop")
    if not close(chain[-1][2], chain[0][1]):
        raise BuildError("loop does not close")
    edges = []
    cur = chain[0][1]
    for k, (kind, s, e, m) in enumerate(chain):
        s = cur
        e = chain[0][1] if k == len(chain) - 1 else e
        if kind == "line":
            edges.append(cq.Edge.makeLine(to_world(s), to_world(e)))
        else:
            edges.append(cq.Edge.makeThreePointArc(to_world(s), to_world(m), to_world(e)))
        cur = e
    return cq.Wire.assembleEdges(edges)


_NORMAL = [None]


def _profile_face(profile, sketch_tf):
    o, xa, ya, za = (_v(sketch_tf["origin"]), _v(sketch_tf["x_axis"]),
                     _v(sketch_tf["y_axis"]), _v(sketch_tf["z_axis"]))
    _NORMAL[0] = za

    def to_world(p):
        return o + xa * p[0] + ya * p[1]

    loops = profile["loops"]
    outer = [l for l in loops if l.get("is_outer")]
    inner = [l for l in loops if not l.get("is_outer")]
    if not outer:
        raise BuildError("no outer loop")
    if len(outer) > 1:  # keep first as outer, treat the rest as holes
        inner = outer[1:] + inner
    ow = _loop_wire(outer[0], to_world)
    iw = [_loop_wire(l, to_world) for l in inner]
    return cq.Face.makeFromWires(ow, iw), za


def _extrude(face, normal, ext):
    typ = ext["extent_type"]
    d1 = ext["extent_one"]["distance"]["value"]
    if typ == "OneSideFeatureExtentType":
        solid = cq.Solid.extrudeLinear(face, normal * d1)
    elif typ == "SymmetricFeatureExtentType":
        solid = cq.Solid.extrudeLinear(face, normal * d1).fuse(
            cq.Solid.extrudeLinear(face, normal * -d1))
    elif typ == "TwoSidesFeatureExtentType":
        d2 = ext["extent_two"]["distance"]["value"]
        solid = cq.Solid.extrudeLinear(face, normal * d1).fuse(
            cq.Solid.extrudeLinear(face, normal * -d2))
    else:
        raise BuildError(f"unknown extent type {typ}")
    return solid


def build_shape(path):
    d = json.load(open(path))
    ents = d["entities"]
    body = None
    for item in d["sequence"]:
        if item["type"] != "ExtrudeFeature":
            continue
        ext = ents[item["entity"]]
        if ext["start_extent"]["type"] != "ProfilePlaneStartDefinition":
            raise BuildError("unsupported start extent")
        op = ext["operation"]
        for k, ref in enumerate(ext["profiles"]):
            sk = ents[ref["sketch"]]
            face, normal = _profile_face(sk["profiles"][ref["profile"]], sk["transform"])
            new = _extrude(face, normal, ext)
            this_op = op if op != "NewBodyFeatureOperation" else ("NewBodyFeatureOperation" if k == 0 else "JoinFeatureOperation")
            if body is None:
                body = new
            elif this_op in ("NewBodyFeatureOperation", "JoinFeatureOperation"):
                body = body.fuse(new)
            elif this_op == "CutFeatureOperation":
                body = body.cut(new)
            elif this_op == "IntersectFeatureOperation":
                body = body.intersect(new)
            else:
                raise BuildError(f"unknown operation {this_op}")
    if body is None:
        raise BuildError("no extrude features")
    # no body.clean(): it can corrupt valid fused solids (seam edges are harmless)
    if not body.isValid():
        raise BuildError("invalid solid")
    if body.Volume() <= 0:
        raise BuildError("zero volume")
    return body
