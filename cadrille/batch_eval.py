"""Run cadrille (img mode, CPU) on several of our dev meshes and score with the paper's protocol.

  python batch_eval.py gen   --ckpt checkpoints/cadrille    --tag sft --n 10
  python batch_eval.py gen   --ckpt checkpoints/cadrille-rl --tag rl  --n 10
  python batch_eval.py score --tag sft
  python batch_eval.py score --tag rl

Scoring follows evaluate.py: predicted mesh is normalised by its own bbox (centre 0.5,
longest side 1), GT is normalised the same way, volumetric IoU via mesh booleans (manifold3d),
Chamfer distance on 8192 sampled points (x1000 reported). An invalid program counts as a failure.
"""
import argparse
import json
import os
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).parent
DATA = HERE.parent / 'data'
GT_DIR = DATA / 'meshes_hidden' / 'dev'


def sample_ids(n):
    ids = [l.strip().split('/')[-1] for l in (DATA / 'splits' / 'dev.txt').read_text().split() if l.strip()]
    ids = [i for i in ids if (GT_DIR / f'{i}.stl').exists()]
    step = max(len(ids) // n, 1)
    return ids[::step][:n]


def load_unit(path):
    m = trimesh.load_mesh(path)
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    m.apply_scale(1.0 / m.extents.max())
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def gen(args):
    import torch
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate
    from run_one import make_grid

    out = HERE / 'work_dirs' / args.tag
    (out / 'py').mkdir(parents=True, exist_ok=True)
    (out / 'inputs').mkdir(exist_ok=True)
    dtype = torch.bfloat16
    model = Cadrille.from_pretrained(str(HERE / args.ckpt), torch_dtype=dtype,
                                     attn_implementation='sdpa', device_map='cpu').eval()
    processor = AutoProcessor.from_pretrained(
        'Qwen/Qwen2-VL-2B-Instruct', min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28,
        padding_side='left')
    for stem in sample_ids(args.n):
        dst = out / 'py' / f'{stem}+0.py'
        if dst.exists():
            continue
        grid = make_grid(load_unit(GT_DIR / f'{stem}.stl'))
        grid.save(out / 'inputs' / f'{stem}.png')
        batch = collate([{'video': [grid], 'description': 'Generate cadquery code', 'file_name': stem}],
                        processor=processor, n_points=256, eval=True)
        t = time.time()
        with torch.no_grad():
            ids = model.generate(
                input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                point_clouds=batch['point_clouds'], is_pc=batch['is_pc'], is_img=batch['is_img'],
                pixel_values_videos=batch['pixel_values_videos'].to(dtype),
                video_grid_thw=batch['video_grid_thw'], max_new_tokens=768)
        txt = processor.batch_decode([ids[0][len(batch['input_ids'][0]):]], skip_special_tokens=True,
                                     clean_up_tokenization_spaces=False)[0]
        dst.write_text(txt)
        print(f'{args.tag} {stem}: {time.time() - t:.0f}s', flush=True)


def py_to_mesh(py_text):
    import cadquery as cq
    ns = {'cq': cq}
    exec(py_text, ns)
    comp = ns['r'].val()
    v, f = comp.tessellate(0.001, 0.1)
    m = trimesh.Trimesh([(p.x, p.y, p.z) for p in v], f)
    assert len(m.faces) > 2
    return m


def iou(gt, pred):
    inter = 0.0
    for a in gt.split():
        for b in pred.split():
            x = a.intersection(b, engine='manifold')
            inter += x.volume if x is not None else 0
    vg = sum(m.volume for m in gt.split())
    vp = sum(m.volume for m in pred.split())
    return inter / (vg + vp - inter)


def chamfer(gt, pred, n=8192):
    from scipy.spatial import cKDTree
    a, _ = trimesh.sample.sample_surface(gt, n)
    b, _ = trimesh.sample.sample_surface(pred, n)
    d1, _ = cKDTree(a).query(b)
    d2, _ = cKDTree(b).query(a)
    return float(np.mean(d1 ** 2) + np.mean(d2 ** 2))


def score(args):
    out = HERE / 'work_dirs' / args.tag
    rows = []
    for py in sorted((out / 'py').glob('*.py')):
        stem = py.stem.split('+')[0]
        row = {'id': stem, 'valid': False, 'iou': None, 'cd_x1000': None}
        try:
            pm = py_to_mesh(py.read_text())
            (out / 'mesh').mkdir(exist_ok=True)
            pm.export(out / 'mesh' / f'{stem}_raw.stl')
            c = (pm.bounds[0] + pm.bounds[1]) / 2
            pm.apply_translation(-c)
            pm.apply_scale(1.0 / pm.extents.max())
            pm.apply_translation([0.5, 0.5, 0.5])
            pm.export(out / 'mesh' / f'{stem}.stl')
            gt = load_unit(GT_DIR / f'{stem}.stl')
            row['valid'] = True
            row['cd_x1000'] = chamfer(gt, pm) * 1000
            row['iou'] = iou(gt, pm)
        except Exception as e:
            row['error'] = f'{type(e).__name__}: {str(e)[:120]}'
        rows.append(row)
        print(row, flush=True)
    ious = [r['iou'] for r in rows if r['iou'] is not None]
    cds = [r['cd_x1000'] for r in rows if r['cd_x1000'] is not None]
    summ = {'tag': args.tag, 'n': len(rows), 'invalid': sum(not r['valid'] for r in rows),
            'iou_scored': len(ious), 'mean_iou': float(np.mean(ious)) if ious else None,
            'median_iou': float(np.median(ious)) if ious else None,
            'median_cd_x1000': float(np.median(cds)) if cds else None}
    print(summ)
    (out / 'scores.json').write_text(json.dumps({'summary': summ, 'rows': rows}, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['gen', 'score'])
    ap.add_argument('--ckpt', default='checkpoints/cadrille')
    ap.add_argument('--tag', default='sft')
    ap.add_argument('--n', type=int, default=10)
    a = ap.parse_args()
    gen(a) if a.mode == 'gen' else score(a)
