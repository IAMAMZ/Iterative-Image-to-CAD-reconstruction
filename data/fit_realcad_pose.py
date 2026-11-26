"""Fit camera + object pose for the RealCAD photos by aligning the GT CAD mesh to the SAM 3 masks.

  python fit_realcad_pose.py --split test50 --n 50                  (resumable; fits land in ../out/pose_fit/<id>)
  python fit_realcad_pose.py --split test50 --ids 00103629 --force   (refit; --top 8 refines more starts)

Uses the GT CAD mesh, so its outputs are an oracle ("perception is free"), never an image-only input.
realcad_gt_inputs.py turns the fits into the data/realcad/<split>_gt split.

Capture model (checked on the photos: the table marks stay put between views, the part turns):
  * one fixed pinhole camera per part: focal f (square pixels, principal point at the image centre), elevation e,
    distance d, small aim / roll correction; world = table, +Z up, table plane z = 0
  * the part rests on the table in one pose: R_rest = (one of 24 axis-aligned rotations) * small residual,
    lifted so its lowest point touches z = 0
  * view k only turns the part about +Z by yaw_k and slides it on the table by (tx_k, ty_k)
Fitting: differentiable point-splat silhouettes vs the SAM masks (soft IoU), all 48 starts (24 rest poses x 2 turn
directions) optimised in one batch at low resolution, best 4 refined at higher resolution, best 1 refined at 384 px,
then polished on the EXACT mesh outline (projected triangles filled, 256 px; Powell, no gradients): the soft splat
outline is 0.5-5 % larger than the exact one, which made the fitted parts come out slightly small.
Capture prior (weak, it breaks ties such as symmetric parts that look the same at any turn): every part was shot the
same way, so elevation ~ N(48.3, 3) deg, focal ~ 752 px +- 3 %, each turn between photos ~ 90 +- 12 deg, all in one
direction (the sign of the start). Values from the 42 well-fitted test50 parts of the first run (out/pose_fit*).
The phone sometimes moved a little between photos (part larger in one photo than one fixed camera allows), so each view
may move the camera along its line of sight: distance d * exp(ldv_k), ldv_k ~ N(0, 5 %).
The final pose is chosen among the top starts by the EXACT outline (384 px) rather than the soft one, which cannot see
small holes: a plate flipped end for end (hole at the wrong end) scores almost the same on the soft outline.
Target per view = the SAM mask; where SAM found nothing, a colour threshold of the photo (saturated or dark pixels,
largest blob, holes filled: the parts are coloured / dark prints on a light grey table), so every view is constrained.
Then the mesh is rasterised exactly at full resolution: mask IoU vs SAM per view, z-depth, overlays.

Object frame = synthetic convention (data/cameras.json): centre = bbox centre, scale = 1 / bounding-sphere radius,
camera poses are OpenGL camera-to-world in that frame, depth is z along the view axis in those units (0 = background).
"""
import argparse
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).parent
RC = HERE / "realcad"
W0, H0 = 1024, 768
F0 = 752.0            # focal prior in px at 1024 wide (median of well-fitted parts; ~69 deg horizontal FOV)
F_SIG = 0.03          # log-focal spread
E0, E_SIG = math.radians(48.3), math.radians(3.0)     # camera elevation prior
STEP_SIG = math.radians(12.0)                         # spread of each turn around +-90 deg
LDV_SIG = 0.05                                        # per-view camera distance change (log), phone moved a little
LAM = 0.002           # prior weight per squared z-score / 2, in units of (1 - IoU): a tie-breaker, not a constraint
POLISH_W, POLISH_EVALS = 256, 600
VIEWS = (1, 2, 3, 4)
torch.set_num_threads(max(1, torch.get_num_threads()))


# ------------------------------------------------------------------ geometry helpers
def rot24():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3))
            for r, (c, s) in enumerate(zip(perm, signs)):
                R[r, c] = s
            if np.linalg.det(R) > 0:
                out.append(R)
    return np.stack(out)


def rodrigues(w):
    """(..., 3) axis-angle -> (..., 3, 3)"""
    th = w.norm(dim=-1, keepdim=True).clamp_min(1e-8)
    k = w / th
    K = torch.zeros(w.shape[:-1] + (3, 3), dtype=w.dtype)
    K[..., 0, 1], K[..., 0, 2] = -k[..., 2], k[..., 1]
    K[..., 1, 0], K[..., 1, 2] = k[..., 2], -k[..., 0]
    K[..., 2, 0], K[..., 2, 1] = -k[..., 1], k[..., 0]
    th = th[..., None]
    return torch.eye(3, dtype=w.dtype) + torch.sin(th) * K + (1 - torch.cos(th)) * K @ K


def rotz(a):
    c, s = torch.cos(a), torch.sin(a)
    z, o = torch.zeros_like(a), torch.ones_like(a)
    return torch.stack([torch.stack([c, -s, z], -1), torch.stack([s, c, z], -1), torch.stack([z, z, o], -1)], -2)


def camera(e, d, wc):
    """World->camera (OpenCV: x right, y down, z forward) for a camera at elevation e, distance d, azimuth 0,
    looking at the origin, then rotated by the small residual wc (in camera axes). Returns R (B,3,3), eye (B,3)."""
    eye = torch.stack([d * torch.cos(e), torch.zeros_like(d), d * torch.sin(e)], -1)
    fwd = -eye / eye.norm(dim=-1, keepdim=True)
    up = torch.tensor([0.0, 0.0, 1.0]).expand_as(fwd)
    right = torch.cross(fwd, up, dim=-1)
    right = right / right.norm(dim=-1, keepdim=True)
    down = torch.cross(fwd, right, dim=-1)
    R = torch.stack([right, down, fwd], -2)            # rows = camera axes in world coords
    return rodrigues(wc) @ R, eye


# ------------------------------------------------------------------ data
def load_part(split, pid, n_pts=20000, seed=0):
    m = trimesh.load(RC / split / "meshes" / f"{pid}.stl")
    centre = (m.bounds[0] + m.bounds[1]) / 2
    radius = float(np.linalg.norm(m.vertices - centre, axis=1).max())
    m.apply_translation(-centre)
    m.apply_scale(1.0 / radius)
    pts, _ = trimesh.sample.sample_surface(m, n_pts, seed=seed)
    masks, source = {}, {}
    for k in VIEWS:
        a = np.asarray(Image.open(RC / split / "images" / pid / "mask" / f"{k}.png").convert("L")) > 127
        assert a.shape == (H0, W0), a.shape
        source[k] = "sam"
        if not a.any():
            a = colour_mask(np.asarray(Image.open(RC / split / "images" / pid / "rgb" / f"{k}.jpg").convert("RGB")))
            source[k] = "colour" if a.any() else "none"
        masks[k] = a
    return m, torch.tensor(pts, dtype=torch.float32), masks, source, {"centre": centre.tolist(), "scale": 1.0 / radius}


def colour_mask(rgb):
    """fallback fit target when SAM found nothing: saturated or dark pixels, largest blob, holes filled"""
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV")).astype(np.float32) / 255
    m = ndimage.binary_opening((hsv[..., 1] > 0.30) | (hsv[..., 2] < 0.25), iterations=2)
    lab, n = ndimage.label(m)
    if n == 0:
        return m
    m = lab == 1 + int(np.argmax(ndimage.sum(m, lab, range(1, n + 1))))
    return ndimage.binary_fill_holes(m)


def down(mask, w):
    """area-average a full-res mask to width w"""
    h = w * H0 // W0
    return torch.tensor(np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize((w, h), Image.BOX)),
                        dtype=torch.float32) / 255


# ------------------------------------------------------------------ model
class Fit:
    """B independent hypotheses fitted in parallel."""

    def __init__(self, R_disc, sign, init, B_views_valid):
        B = len(R_disc)
        self.R_disc = torch.tensor(R_disc, dtype=torch.float32)
        self.w_rest = torch.zeros(B, 3, requires_grad=True)
        steps = torch.tensor([0.0, 1.0, 2.0, 3.0])
        self.sign = torch.tensor(sign, dtype=torch.float32)
        self.yaw = (torch.tensor(sign, dtype=torch.float32)[:, None] * steps * math.pi / 2).clone().requires_grad_(True)
        self.txy = init["txy"].expand(B, 4, 2).clone().requires_grad_(True)
        self.log_f = torch.full((B,), math.log(init["f"])).requires_grad_(True)
        self.e = torch.full((B,), init["e"]).requires_grad_(True)
        self.log_d = torch.full((B,), math.log(init["d"])).requires_grad_(True)
        self.wc = torch.zeros(B, 3, requires_grad=True)
        self.ldv = torch.zeros(B, 4, requires_grad=True)
        self.valid = B_views_valid

    def params(self):
        return [self.w_rest, self.yaw, self.txy, self.log_f, self.e, self.log_d, self.wc, self.ldv]

    def subset(self, idx):
        for name in ("R_disc", "sign", "w_rest", "yaw", "txy", "log_f", "e", "log_d", "wc", "ldv"):
            t = getattr(self, name)[idx].detach().clone()
            setattr(self, name, t.requires_grad_(name not in ("R_disc", "sign")))
        return self

    def world_points(self, pts):
        """(N,3) object points -> (B,4,N,3) world points"""
        R = rodrigues(self.w_rest) @ self.R_disc                     # (B,3,3)
        p = torch.einsum("bij,nj->bni", R, pts)                      # (B,N,3)
        p = p - torch.stack([torch.zeros_like(p[..., 0]), torch.zeros_like(p[..., 0]),
                             p[..., 2].min(dim=1, keepdim=True).values.expand_as(p[..., 2])], -1)
        Rz = rotz(self.yaw)                                          # (B,4,3,3)
        q = torch.einsum("bvij,bnj->bvni", Rz, p)
        t = torch.cat([self.txy, torch.zeros_like(self.txy[..., :1])], -1)
        return q + t[:, :, None, :]

    def project(self, pts, w):
        s = w / W0
        Rc, eye = camera(self.e, torch.exp(self.log_d), self.wc)
        eye_v = eye[:, None, :] * torch.exp(self.ldv)[..., None]       # (B,4,3): camera moved along its sight line
        X = self.world_points(pts) - eye_v[:, :, None, :]
        Xc = torch.einsum("bij,bvnj->bvni", Rc, X)
        z = Xc[..., 2].clamp_min(1e-3)
        f = torch.exp(self.log_f)[:, None, None] * s
        u = f * Xc[..., 0] / z + w / 2
        v = f * Xc[..., 1] / z + (w * H0 // W0) / 2
        return u, v

    def soft_sil(self, pts, w, blur):
        h = w * H0 // W0
        u, v = self.project(pts, w)
        B, V, N = u.shape
        u, v = u - 0.5, v - 0.5
        x0, y0 = torch.floor(u), torch.floor(v)
        img = torch.zeros(B * V * h * w)
        base = (torch.arange(B * V).view(B, V, 1) * h * w)
        for dx in (0, 1):
            for dy in (0, 1):
                xi, yi = x0 + dx, y0 + dy
                wt = (1 - (u - xi).abs()) * (1 - (v - yi).abs())
                ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
                idx = (base + yi.clamp(0, h - 1).long() * w + xi.clamp(0, w - 1).long())[ok]
                img = img.index_add(0, idx, wt[ok])
        img = img.view(B * V, 1, h, w)
        if blur > 0:
            r = int(math.ceil(2.5 * blur))
            g = torch.exp(-torch.arange(-r, r + 1, dtype=torch.float32) ** 2 / (2 * blur ** 2))
            g = g / g.sum()
            img = torch.nn.functional.conv2d(img, g.view(1, 1, 1, -1), padding=(0, r))
            img = torch.nn.functional.conv2d(img, g.view(1, 1, -1, 1), padding=(r, 0))
        return img.view(B, V, h, w)

    def loss(self, pts, targets, w, blur):
        dens = self.soft_sil(pts, w, blur)
        area = targets.sum(dim=(-1, -2)).clamp_min(1.0)                      # (V,) mask areas at this res
        tau = 0.15 * len(pts) / area.mean()                                   # density that counts as "covered"
        occ = 1 - torch.exp(-dens / tau)
        inter = (occ * targets).sum(dim=(-1, -2))
        union = (occ + targets - occ * targets).sum(dim=(-1, -2))
        iou = inter / union.clamp_min(1e-6)                                   # (B,V)
        valid = self.valid.float()
        l_iou = ((1 - iou) * valid).sum(-1) / valid.sum()
        return l_iou + capture_prior(self.e, self.log_f, self.yaw, self.sign, self.w_rest, self.wc, self.ldv), iou


def capture_prior(e, log_f, yaw, sign, w_rest, wc, ldv):
    """(B,) penalty: elevation, focal and turn steps near the usual capture; small rest / aim residuals"""
    d = yaw[:, 1:] - yaw[:, :-1] - sign[:, None] * math.pi / 2
    d = torch.atan2(torch.sin(d), torch.cos(d))                        # wrapped step error
    z2 = ((e - E0) / E_SIG) ** 2 + ((log_f - math.log(F0)) / F_SIG) ** 2 + ((d / STEP_SIG) ** 2).sum(-1) \
        + ((ldv / LDV_SIG) ** 2).sum(-1)
    return 0.5 * LAM * z2 + 0.5 * (w_rest ** 2).sum(-1) + 0.5 * (wc ** 2).sum(-1)


def optimise(fit, pts, masks, w, blur, steps, lr=0.03):
    targets = torch.stack([down(masks[k], w) for k in VIEWS])
    opt = torch.optim.Adam([{"params": [fit.yaw, fit.w_rest, fit.wc, fit.e], "lr": lr},
                            {"params": [fit.txy], "lr": lr * 0.5},
                            {"params": [fit.log_f, fit.log_d, fit.ldv], "lr": lr * 0.5}])
    for _ in range(steps):
        opt.zero_grad()
        L, iou = fit.loss(pts, targets, w, blur)
        L.sum().backward()
        opt.step()
        with torch.no_grad():
            fit.e.clamp_(math.radians(5), math.radians(85))
    with torch.no_grad():
        L, iou = fit.loss(pts, targets, w, blur)
    return L.detach(), iou.detach()


def initial_guess(masks):
    """focal and elevation priors, distance from the mask size, per-view table offsets from mask centroids."""
    f, e = F0, E0
    sizes, cents = [], []
    for k in VIEWS:
        m = masks[k]
        if m.any():
            ys, xs = np.nonzero(m)
            sizes.append(max(np.ptp(xs), np.ptp(ys)))
            cents.append((xs.mean(), ys.mean()))
        else:
            cents.append(None)
    r_px = 0.5 * float(np.median(sizes))
    d = f * 0.8 / r_px
    # back-project each centroid onto the table plane z = 0 (camera at azimuth 0 looking at the origin)
    Rc, eye = camera(torch.tensor([e]), torch.tensor([d]), torch.zeros(1, 3))
    Rc, eye = Rc[0].numpy(), eye[0].numpy()
    txy = []
    for c in cents:
        if c is None:
            txy.append((0.0, 0.0))
            continue
        ray = Rc.T @ np.array([(c[0] - W0 / 2) / f, (c[1] - H0 / 2) / f, 1.0])
        lam = -eye[2] / ray[2]
        p = eye + lam * ray
        txy.append((float(p[0]), float(p[1])))
    return {"f": f, "e": e, "d": d, "txy": torch.tensor(txy, dtype=torch.float32)[None]}


# ------------------------------------------------------------------ exact raster (numpy z-buffer)
def raster(mesh_world, Rc, eye, f, w=W0, h=H0):
    """mesh vertices already in world coords; returns depth (h,w) float32 with 0 = background (z along view axis)"""
    X = (mesh_world.vertices - eye) @ Rc.T
    z = X[:, 2]
    u = f * X[:, 0] / z + w / 2
    v = f * X[:, 1] / z + h / 2
    depth = np.full((h, w), np.inf)
    for tri in mesh_world.faces:
        zs = z[tri]
        if (zs <= 1e-6).any():
            continue
        xs, ys = u[tri], v[tri]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), w - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), h - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        dd = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(dd) < 1e-12:
            continue
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / dd
        b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / dd
        c = 1 - a - b
        inside = (a >= 0) & (b >= 0) & (c >= 0)
        if not inside.any():
            continue
        zi = 1.0 / (a / zs[0] + b / zs[1] + c / zs[2])        # perspective-correct z
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (zi < sub)
        sub[upd] = zi[upd]
    depth[~np.isfinite(depth)] = 0
    return depth.astype(np.float32)


def capture_dev(fit):
    """how far this fit is from the usual capture, in degrees / percent (for QA)"""
    with torch.no_grad():
        d = fit.yaw[0, 1:] - fit.yaw[0, :-1] - fit.sign[0] * math.pi / 2
        d = torch.atan2(torch.sin(d), torch.cos(d))
        return {"elevation_dev_deg": round(math.degrees(float(fit.e[0] - E0)), 2),
                "focal_dev_%": round(100 * (math.exp(float(fit.log_f[0])) / F0 - 1), 2),
                "turn_step_dev_deg": [round(math.degrees(float(x)), 1) for x in d],
                "turn_direction": int(fit.sign[0]),
                "view_distance_%": [round(100 * (math.exp(float(x)) - 1), 1) for x in fit.ldv[0]]}


def outline(m):
    return m & ~ndimage.binary_erosion(m, iterations=2)


# ------------------------------------------------------------------ exact-outline polish
PARAMS = (("w_rest", 3), ("yaw", 4), ("txy", 8), ("log_f", 1), ("e", 1), ("log_d", 1), ("wc", 3), ("ldv", 4))


def get_x(fit, b=0):
    return np.concatenate([getattr(fit, n)[b].detach().double().numpy().ravel() for n, _ in PARAMS])


def set_x(fit, x):
    i = 0
    for n, k in PARAMS:
        t = getattr(fit, n)
        with torch.no_grad():
            t[0] = torch.tensor(x[i:i + k], dtype=t.dtype).view(t[0].shape)
        i += k


def unpack(fit, x, b=0):
    """parameter vector -> dict of float tensors, camera (Rc, eye per view (4,3)), focal, R_rest (numpy)"""
    i, out = 0, {}
    for n, k in PARAMS:
        out[n] = torch.tensor(x[i:i + k], dtype=torch.float32)
        i += k
    Rc, eye = camera(out["e"], torch.exp(out["log_d"]), out["wc"][None])
    R_rest = (rodrigues(out["w_rest"][None]) @ fit.R_disc[b:b + 1])[0].double()
    eyes = eye[0].double().numpy()[None] * np.exp(out["ldv"].double().numpy())[:, None]
    return out, Rc[0].double().numpy(), eyes, float(torch.exp(out["log_f"])), R_rest.numpy()


def exact_sils(mesh, Rc, eyes, f, R_rest, yaw, txy, w):
    """filled projected triangles = exact silhouette per view at width w (bool arrays)"""
    h = w * H0 // W0
    s = w / W0
    v_rest = mesh.vertices @ R_rest.T
    v_rest[:, 2] -= v_rest[:, 2].min()
    sils = []
    for i in range(4):
        c, sn = math.cos(yaw[i]), math.sin(yaw[i])
        vw = v_rest @ np.array([[c, -sn, 0], [sn, c, 0], [0, 0, 1]]).T + np.array([txy[i, 0], txy[i, 1], 0])
        X = (vw - eyes[i]) @ Rc.T
        z = np.clip(X[:, 2], 1e-3, None)
        uv = np.stack([f * s * X[:, 0] / z + w / 2, f * s * X[:, 1] / z + h / 2], 1)
        tri = uv[mesh.faces]                                            # (F,3,2)
        area = (tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) \
            - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1])
        keep = area > 0 if (area > 0).sum() >= (area < 0).sum() else area < 0   # one side covers a closed mesh
        im = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(im)
        for t in tri[keep]:
            d.polygon([tuple(q) for q in t], fill=1)
        sils.append(np.asarray(im, dtype=bool))
    return sils


def exact_objective(fit, mesh, masks, valid, w, b=0):
    """x -> (1 - mean exact IoU) + capture prior, for candidate b of the batch"""
    tg = [down(masks[k], w).numpy() > 0.5 for k in VIEWS]
    ok = valid.numpy()
    sign = fit.sign[b:b + 1]

    def obj(x):
        p, Rc, eyes, f, R_rest = unpack(fit, x, b)
        sils = exact_sils(mesh, Rc, eyes, f, R_rest, p["yaw"].numpy(), p["txy"].numpy().reshape(4, 2), w)
        ious = [(m & t).sum() / max((m | t).sum(), 1) for m, t, o in zip(sils, tg, ok) if o]
        pr = capture_prior(p["e"], p["log_f"], p["yaw"][None], sign, p["w_rest"][None], p["wc"][None],
                           p["ldv"][None])
        return 1 - float(np.mean(ious)) + float(pr[0])
    return obj


def polish(fit, mesh, masks, valid, w=POLISH_W, evals=POLISH_EVALS):
    """minimise (1 - mean exact IoU) + capture prior over all 25 parameters, starting from the gradient fit"""
    from scipy.optimize import minimize
    obj = exact_objective(fit, mesh, masks, valid, w)
    x0 = get_x(fit)
    f0 = obj(x0)
    r = minimize(obj, x0, method="Powell", options={"maxfev": evals, "xtol": 1e-3, "ftol": 1e-5})
    if r.fun < f0:
        set_x(fit, r.x)
    return f0, min(f0, float(r.fun))


# ------------------------------------------------------------------ per part
def fit_part(split, pid, out, log, top=4):
    t0 = time.time()
    mesh, pts, masks, source, norm = load_part(split, pid)
    valid = torch.tensor([masks[k].any() for k in VIEWS])
    if not valid.any():
        log(f"{pid}: no masks, skipped")
        return None
    init = initial_guess(masks)
    R = rot24()
    R_disc = np.concatenate([R, R])
    sign = [1.0] * 24 + [-1.0] * 24
    fit = Fit(R_disc, sign, init, valid)
    pts_c = pts[:4000]
    L, _ = optimise(fit, pts_c, masks, 96, 1.5, 150, lr=0.05)
    fit.subset(torch.argsort(L)[:top])
    L, _ = optimise(fit, pts[:10000], masks, 192, 1.0, 200, lr=0.02)
    exact = [exact_objective(fit, mesh, masks, valid, 384, b)(get_x(fit, b)) for b in range(len(L))]
    best = int(np.argmin(exact))                       # exact outline sees holes the soft one blurs away
    fit.subset(torch.tensor([best]))
    L, soft_iou = optimise(fit, pts, masks, 384, 0.7, 150, lr=0.01)
    obj_before, obj_after = polish(fit, mesh, masks, valid)

    # ---- exact render at full resolution
    with torch.no_grad():
        Rc, eye = camera(fit.e, torch.exp(fit.log_d), fit.wc)
        Rc, eye = Rc[0].double().numpy(), eye[0].double().numpy()
        eyes = eye[None] * np.exp(fit.ldv[0].double().numpy())[:, None]
        f = float(torch.exp(fit.log_f)[0])
        R_rest = (rodrigues(fit.w_rest) @ fit.R_disc)[0].double().numpy()
        yaw = fit.yaw[0].double().numpy()
        txy = fit.txy[0].double().numpy()
    v_rest = mesh.vertices @ R_rest.T
    zoff = -v_rest[:, 2].min()
    K = np.array([[f, 0, W0 / 2], [0, f, H0 / 2], [0, 0, 1]])
    cv2gl = np.diag([1.0, -1.0, -1.0, 1.0])
    views, depths, ious = {}, {}, {}
    out_p = out / pid
    (out_p / "mask_cad").mkdir(parents=True, exist_ok=True)
    tiles = []
    for i, k in enumerate(VIEWS):
        Rz = np.array([[math.cos(yaw[i]), -math.sin(yaw[i]), 0], [math.sin(yaw[i]), math.cos(yaw[i]), 0], [0, 0, 1]])
        T = np.eye(4)                                                      # world <- object
        T[:3, :3] = Rz @ R_rest
        T[:3, 3] = Rz @ np.array([0, 0, zoff]) + np.array([txy[i, 0], txy[i, 1], 0])
        mw = mesh.copy()
        mw.apply_transform(T)
        dep = raster(mw, Rc, eyes[i], f)
        c2w_world = np.eye(4)
        c2w_world[:3, :3], c2w_world[:3, 3] = Rc.T, eyes[i]               # OpenCV camera-to-world, this view
        sil = dep > 0
        sam = masks[k]                                                     # fit target (SAM or colour fallback)
        iou = float((sil & sam).sum() / max((sil | sam).sum(), 1)) if sam.any() else None
        silf = ndimage.binary_fill_holes(sil)                              # for old, hole-filled SAM masks
        iou_f = float((silf & sam).sum() / max((silf | sam).sum(), 1)) if sam.any() else None
        c2w_obj_gl = np.linalg.inv(T) @ c2w_world @ cv2gl
        views[str(k)] = {"c2w": c2w_obj_gl.round(6).tolist(), "yaw_deg": round(math.degrees(yaw[i]), 2),
                         "table_xy": txy[i].round(4).tolist(), "mask_iou": None if iou is None else round(iou, 4),
                         "mask_iou_filled": None if iou_f is None else round(iou_f, 4),
                         "target": source[k], "sam_mask_empty": source[k] != "sam"}
        depths[str(k)] = dep.astype(np.float16)
        ious[k] = iou
        Image.fromarray(sil.astype(np.uint8) * 255).save(out_p / "mask_cad" / f"{k}.png")
        # overlay: SAM outline green, CAD outline red
        rgb = np.asarray(Image.open(RC / split / "images" / pid / "rgb" / f"{k}.jpg").convert("RGB")).copy()
        rgb[outline(sam)] = [0, 255, 0]
        rgb[outline(sil)] = [255, 0, 0]
        t = Image.fromarray(rgb).resize((512, 384))
        ImageDraw.Draw(t).text((6, 6), f"view {k}  IoU {'-' if iou is None else f'{iou:.3f}'}  filled "
                               f"{'-' if iou_f is None else f'{iou_f:.3f}'}  ({source[k]})", fill=(255, 0, 0))
        tiles.append(t)
    sheet = Image.new("RGB", (1024, 768))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 2) * 512, (i // 2) * 384))
    sheet.save(out_p / "overlay.jpg", quality=88)
    np.savez_compressed(out_p / "depth.npz", **depths)
    vi = [v for v in ious.values() if v is not None]
    rec = {"id": pid, "split": split,
           "frame": "object normalised to unit bounding sphere (centre = bbox centre), +Z = CAD +Z; c2w are OpenGL "
                    "camera-to-world in this frame; depth.npz = z along the view axis in these units, 0 = background",
           **norm, "image_size": [W0, H0], "K": K.round(4).tolist(),
           "camera": {"focal_px": round(f, 2), "elevation_deg": round(math.degrees(float(fit.e[0].detach())), 2),
                      "distance": round(float(torch.exp(fit.log_d[0].detach())), 4)},
           "R_rest": R_rest.round(6).tolist(), "views": views,
           "mean_mask_iou": round(float(np.mean(vi)), 4), "min_mask_iou": round(float(np.min(vi)), 4),
           "top_starts": top,
           "soft_iou_final": [round(float(x), 4) for x in soft_iou[0]],
           "polish_objective": [round(obj_before, 4), round(obj_after, 4)],
           "capture": capture_dev(fit), "fit_seconds": round(time.time() - t0, 1)}
    (out_p / "pose.json").write_text(json.dumps(rec, indent=1))
    log(f"{pid}: mean IoU {rec['mean_mask_iou']:.3f} min {rec['min_mask_iou']:.3f}  f {f:.0f}px "
        f"elev {rec['camera']['elevation_deg']:.1f}  yaws {[views[str(k)]['yaw_deg'] for k in VIEWS]}  "
        f"{rec['fit_seconds']:.0f}s")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test50")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", default=str(HERE.parent / "out" / "pose_fit"))
    ap.add_argument("--force", action="store_true", help="refit even if pose.json exists")
    ap.add_argument("--top", type=int, default=4, help="starts kept after the coarse stage")
    a = ap.parse_args()
    ids = a.ids or [l.strip().split("/")[-1] for l in (RC / a.split / "ids.txt").read_text().split() if l.strip()][:a.n]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "fit_log.txt", "a")

    def log(s):
        print(s, flush=True)
        logf.write(s + "\n")
        logf.flush()
    for pid in ids:
        if (out / pid / "pose.json").exists() and not a.force:   # resumable: already fitted
            continue
        torch.manual_seed(0)
        fit_part(a.split, pid, out, log, a.top)


if __name__ == "__main__":
    main()
