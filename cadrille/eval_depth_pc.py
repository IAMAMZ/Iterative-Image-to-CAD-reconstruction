"""cadrille in point-cloud mode, fed with point clouds back-projected from the rendered depth maps.

  python eval_depth_pc.py build --n 50                      # depth.npz -> work_dirs/depth_pc/<variant>/<id>.npy (+ previews)
  python eval_depth_pc.py gen   --variant depth4 --n 50     # -> work_dirs/f360_<variant>_dev/py/<id>.py
  python eval_depth_pc.py score --variant depth4 --n 50     # same scorer as eval_fusion360.py
  python eval_depth_pc.py table --variants depth4 depth1 meshpc --n 50   # + the old image run rl_dev

Variants (all 256 points, FPS from 8192, xyz only, scaled to [-1, 1] by their own bbox as in dataset.py test mode):
  depth4  all 4 "table" depth views fused (top_left/right/front/back, all from 45 deg above) - no underside
  depth1  one depth view only (top_front) - a single RGB-D / depth-camera shot
  meshpc  points sampled from the whole GT mesh surface - the paper's own pc protocol (reference)

Depth -> 3D: depth.npz holds z along the view axis (0 = background) for the 512x512 pinhole cameras of
data/cameras.json (OpenGL camera-to-world poses). Points are lifted to the render frame, then R_table and the
unit-sphere normalisation from poses/<id>.json are undone, so they live in the original mesh frame (the frame the
GT is scored in, and the frame the old image run rendered from). I.e. the object pose is assumed known.

Raw meshes and checkpoints are git-ignored; point F360_SRC / --ckpt at a checkout that has them.
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np

import eval_fusion360 as ef

HERE = Path(__file__).parent
DATA = HERE.parent / 'data'
SPLIT_DIR = DATA / 'fusion360' / 'dev'
PC_DIR = HERE / 'work_dirs' / 'depth_pc'
VARIANTS = ('depth4', 'depth1', 'meshpc')
TABLE_VIEWS = ('top_left', 'top_right', 'top_front', 'top_back')
N_PRE, N_POINTS = 8192, 256


def ids(n):
    ef.SPLIT = 'dev'
    return ef.test_ids(n)


# ------------------------------------------------------------------ geometry
def fps(x, k, seed=0):
    """Furthest point sampling (same result family as pytorch3d.sample_farthest_points)."""
    rng = np.random.default_rng(seed)
    idx = np.empty(k, int)
    idx[0] = rng.integers(len(x))
    d = np.full(len(x), np.inf)
    for i in range(1, k):
        d = np.minimum(d, ((x - x[idx[i - 1]]) ** 2).sum(1))
        idx[i] = int(d.argmax())
    return x[idx]


def backproject(depth, pose, fx, fy, cx, cy):
    v, u = np.nonzero(depth > 0)
    z = depth[v, u].astype(np.float64)
    cam = np.stack([(u + 0.5 - cx) * z / fx, (cy - (v + 0.5)) * z / fy, -z], 1)   # inverse of render_fusion360.rasterise
    return cam @ pose[:3, :3].T + pose[:3, 3]


def depth_points(name, views):
    cams = json.loads((DATA / 'cameras.json').read_text())
    k = cams['intrinsics']
    pose_rec = json.loads((SPLIT_DIR / 'poses' / f'{name}.json').read_text())
    dz = np.load(SPLIT_DIR / 'images' / name / 'depth.npz')
    pts = np.concatenate([backproject(dz[v], np.array(cams['views'][v]['pose']), k['fx'], k['fy'], k['cx'], k['cy'])
                          for v in views])
    r_table = np.array(pose_rec['R_table'])
    pts = pts @ r_table                                   # undo posing (p_posed = R p)
    return pts / pose_rec['scale'] + np.array(pose_rec['centre'])   # undo unit-sphere normalisation


def to_model_input(pts, seed=0):
    rng = np.random.default_rng(seed)
    if len(pts) > N_PRE:
        pts = pts[rng.choice(len(pts), N_PRE, replace=False)]
    pts = fps(pts, N_POINTS, seed)
    lo, hi = pts.min(0), pts.max(0)
    pts = (pts - (lo + hi) / 2) / (hi - lo).max() + 0.5   # unit cube, like batch_eval.load_unit
    return ((pts - 0.5) * 2).astype(np.float32)            # dataset.get_point_cloud test mode


def build(args):
    import trimesh
    for v in VARIANTS:
        (PC_DIR / v).mkdir(parents=True, exist_ok=True)
    stats = []
    for name in ids(args.n):
        raw = {'depth4': depth_points(name, TABLE_VIEWS), 'depth1': depth_points(name, ('top_front',))}
        gt = trimesh.load_mesh(ef.SRC / f'{name}.stl')
        raw['meshpc'] = trimesh.sample.sample_surface(gt, N_PRE, seed=0)[0]
        # sanity: depth points must lie on the GT surface (distance in units of the GT bbox diagonal)
        diag = float(np.linalg.norm(gt.extents))
        s = {'id': name}
        for v, p in raw.items():
            np.save(PC_DIR / v / f'{name}.npy', to_model_input(p))
            if v != 'meshpc':
                sub = p[np.random.default_rng(0).choice(len(p), min(2000, len(p)), replace=False)]
                _, dist, _ = trimesh.proximity.closest_point(gt, sub)
                s[f'{v}_n_px'] = len(p)
                s[f'{v}_surf_err_max_rel'] = float(dist.max() / diag)
                # how much of the GT surface the depth sees: share of GT samples within 1% diag of a depth point
                from scipy.spatial import cKDTree
                d, _ = cKDTree(p).query(raw['meshpc'])
                s[f'{v}_coverage'] = float((d < 0.01 * diag).mean())
        stats.append(s)
        print(json.dumps(s), flush=True)
    (PC_DIR / 'build_stats.json').write_text(json.dumps(stats, indent=1))
    preview(ids(min(args.n, 6)))


def preview(names):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(3 * len(VARIANTS), 3 * len(names)))
    for r, name in enumerate(names):
        for c, v in enumerate(VARIANTS):
            p = np.load(PC_DIR / v / f'{name}.npy')
            ax = fig.add_subplot(len(names), len(VARIANTS), r * len(VARIANTS) + c + 1, projection='3d')
            ax.scatter(p[:, 0], p[:, 1], p[:, 2], s=3, c=p[:, 2], cmap='viridis')
            ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_zlim(-1, 1)
            ax.set_axis_off()
            ax.set_title(f'{v}\n{name}' if r == 0 else name, fontsize=7)
    fig.tight_layout()
    fig.savefig(PC_DIR / 'preview.png', dpi=110)


# ------------------------------------------------------------------ generation
def gen(args):
    import time
    import torch
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate

    tag = f'{args.variant}_dev'
    out = ef.workdir(tag)
    (out / 'py').mkdir(parents=True, exist_ok=True)
    todo = [i for i in ids(args.n) if not (out / 'py' / f'{i}.py').exists()]
    print(f'{tag}: {len(todo)} parts to generate', flush=True)
    if not todo:
        return
    dtype = torch.bfloat16
    model = Cadrille.from_pretrained(args.ckpt, torch_dtype=dtype, attn_implementation='sdpa',
                                     device_map='cpu').eval()
    processor = AutoProcessor.from_pretrained('Qwen/Qwen2-VL-2B-Instruct', min_pixels=256 * 28 * 28,
                                              max_pixels=1280 * 28 * 28, padding_side='left')
    stop_ids = {processor.tokenizer.pad_token_id, processor.tokenizer.eos_token_id, 151645, 151643}
    t_all = time.time()
    for b in range(0, len(todo), args.bs):
        names = todo[b:b + args.bs]
        items = [{'point_cloud': np.load(PC_DIR / args.variant / f'{n}.npy'),
                  'description': 'Generate cadquery code', 'file_name': n} for n in names]
        batch = collate(items, processor=processor, n_points=N_POINTS, eval=True)
        t = time.time()
        with torch.no_grad():
            g = model.generate(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                               point_clouds=batch['point_clouds'], is_pc=batch['is_pc'], is_img=batch['is_img'],
                               pixel_values_videos=None, video_grid_thw=None, max_new_tokens=ef.MAX_NEW_TOKENS)
        dt = time.time() - t
        gen_ids = g[:, batch['input_ids'].shape[1]:]
        texts = processor.batch_decode(gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        with open(out / 'gen_meta.jsonl', 'a') as mf:
            for n, gi, txt in zip(names, gen_ids, texts):
                ntok = int(sum(int(x) not in stop_ids for x in gi))
                (out / 'py' / f'{n}.py').write_text(txt)
                mf.write(json.dumps({'id': n, 'n_tokens': ntok, 'hit_limit': ntok >= ef.MAX_NEW_TOKENS,
                                     'batch_s': round(dt, 1), 'batch_size': len(names)}) + '\n')
        done = b + len(names)
        print(f'{tag} {done}/{len(todo)}  batch {dt:.0f}s  eta {(time.time() - t_all) / done * (len(todo) - done) / 60:.0f} min',
              flush=True)


def score(args):
    ef.SPLIT = 'dev'
    ef.score(argparse.Namespace(tag=f'{args.variant}_dev', jobs=args.jobs, limit=args.n))


# ------------------------------------------------------------------ comparison table
def table(args):
    names = ids(args.n)
    tags = ['rl_dev'] + [f'{v}_dev' for v in args.variants]
    labels = {'rl_dev': 'img (old run)', 'depth4_dev': 'depth 4 views', 'depth1_dev': 'depth 1 view',
              'meshpc_dev': 'full mesh pc'}
    per = {}
    for t in tags:
        p = ef.workdir(t) / 'scores.json'
        per[t] = {r['id']: r for r in json.loads(p.read_text())} if p.exists() else {}
    stats = {t: ef._stats([per[t][i] for i in names if i in per[t]], len(names)) for t in tags}
    bstats = {s['id']: s for s in json.loads((PC_DIR / 'build_stats.json').read_text())}
    keys = [('valid', 'valid programs'), ('IR_%', 'IR %'), ('mean_IoU_valid_%', 'mean IoU % (valid only)'),
            ('mean_IoU_invalid_as_0_%', 'mean IoU % (invalid = 0)'), ('median_IoU_%', 'median IoU %'),
            ('p10_IoU_%', '10th-pct IoU %'), ('median_CD_x1000', 'median CD x1000'),
            ('mean_CD_x1000', 'mean CD x1000'), ('mean_tokens', 'mean tokens')]
    L = ['# cadrille-rl on depth-derived point clouds vs the old 4-view image run', '',
         f'First {len(names)} parts of `data/fusion360/dev/ids.txt`. Same scorer as `eval_fusion360.py` '
         '(bbox-normalised GT and prediction, volumetric IoU, Chamfer x1000 on 8192 pts). Checkpoint `cadrille-rl`, '
         'greedy, CPU bf16. `img (old run)` = existing `work_dirs/f360_rl_dev` scores, restricted to these parts.', '',
         '| metric | ' + ' | '.join(labels[t] for t in tags) + ' |', '|---|' + '---|' * len(tags)]
    for k, lab in keys:
        L.append(f'| {lab} | ' + ' | '.join('-' if stats[t][k] is None else
                                            (str(stats[t][k]) if isinstance(stats[t][k], int) else f'{stats[t][k]:.2f}')
                                            for t in tags) + ' |')
    cov4 = np.mean([bstats[i]['depth4_coverage'] for i in names])
    cov1 = np.mean([bstats[i]['depth1_coverage'] for i in names])
    L += ['', f'Depth coverage of the GT surface (share of GT surface samples within 1% of the bbox diagonal of a '
          f'depth point): depth4 {100 * cov4:.0f}%, depth1 {100 * cov1:.0f}%.', '']
    # paired comparison vs the old image run
    L += ['## Paired vs old image run (IoU, invalid = 0)', '', '| variant | better | worse | tie (|d|<1pt) | mean d IoU pts |',
          '|---|---|---|---|---|']
    def iou0(r):
        return 0.0 if (r is None or r['iou'] is None) else 100 * r['iou']
    for t in tags[1:]:
        d = np.array([iou0(per[t].get(i)) - iou0(per['rl_dev'].get(i)) for i in names])
        L.append(f'| {labels[t]} | {(d >= 1).sum()} | {(d <= -1).sum()} | {(abs(d) < 1).sum()} | {d.mean():+.2f} |')
    L += ['', '## Per part (IoU %, - = invalid)', '',
          '| part | ' + ' | '.join(labels[t] for t in tags) + ' | depth4 cov % | depth1 cov % |',
          '|---|' + '---|' * (len(tags) + 2)]
    for i in names:
        cells = []
        for t in tags:
            r = per[t].get(i)
            cells.append('n/a' if r is None else ('-' if r['iou'] is None else f'{100 * r["iou"]:.1f}'))
        L.append(f'| {i} | ' + ' | '.join(cells) +
                 f' | {100 * bstats[i]["depth4_coverage"]:.0f} | {100 * bstats[i]["depth1_coverage"]:.0f} |')
    (HERE / 'results').mkdir(exist_ok=True)
    (HERE / 'results' / 'fusion360_dev_depth_pc.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (HERE / 'results' / 'fusion360_dev_depth_pc_summary.json').write_text(json.dumps(stats, indent=1))
    print('\n'.join(L[:40]))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['build', 'gen', 'score', 'table'])
    ap.add_argument('--n', type=int, default=50)
    ap.add_argument('--variant', choices=VARIANTS, default='depth4')
    ap.add_argument('--variants', nargs='+', default=list(VARIANTS))
    ap.add_argument('--ckpt', default=str(HERE / 'checkpoints' / 'cadrille-rl'))
    ap.add_argument('--bs', type=int, default=8)
    ap.add_argument('--jobs', type=int, default=8)
    a = ap.parse_args()
    {'build': build, 'gen': gen, 'score': score, 'table': table}[a.mode](a)
