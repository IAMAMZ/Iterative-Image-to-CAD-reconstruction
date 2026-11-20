"""Run cadrille (4-view image mode, CPU) on the real RealCAD photos and score up to rotation + uniform scale.

  python eval_realcad.py inputs --n 20                       # photos -> work_dirs/realcad_inputs/<id>.png (2x2 grids)
  python eval_realcad.py gen    --n 20 --ckpt <dir> --tag rl_dev
  python eval_realcad.py score  --n 20 --tag rl_dev
  python eval_realcad.py table  --n 20 --tags rl_dev

Input : data/realcad/dev/images/<id>/rgb/{1..4}.jpg (real photos; camera and object pose unknown)
        Each photo is cropped to a square around the part (dark print on a light table, Otsu threshold on
        brightness, 30% margin), resized to 128 px, given a 3 px black border and tiled 2x2 like
        dataset.CadRecodeDataset.get_img. The photos are NOT the training views (cube diagonals, yellow
        shading, white background), so this is an out-of-distribution test of the model as is.
Score : prediction and GT normalised into the unit cube by bbox (paper protocol). Because the photos fix no
        frame, the prediction is also tried under the 24 axis-aligned rotations (re-normalised after each);
        the rotation with the lowest Chamfer distance is kept and IoU is computed there ("aligned").
        "raw" = the paper protocol with no rotation search.
"""
import argparse
import itertools
import json
import multiprocessing as mp
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

import batch_eval as be

HERE = Path(__file__).parent
RC = HERE.parent / 'data' / 'realcad'
SPLIT = 'dev'
MAX_NEW_TOKENS = 768
SCORE_TIMEOUT_S = 300
IN_DIR = HERE / 'work_dirs' / 'realcad_inputs'


def ids(n=None):
    out = [l.strip().split('/')[-1] for l in (RC / SPLIT / 'ids.txt').read_text().split() if l.strip()]
    out = [i for i in out if (RC / SPLIT / 'meshes' / f'{i}.stl').exists()]
    return out[:n]


def workdir(tag):
    return HERE / 'work_dirs' / f'realcad_{tag}'


# ------------------------------------------------------------------ inputs
def otsu(x):
    hist, edges = np.histogram(x, 256, (0, 256))
    p = hist / hist.sum()
    w = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    between = (mu[-1] * w - mu) ** 2 / np.maximum(w * (1 - w), 1e-12)
    return int(np.argmax(between))


def crop_photo(path, size=128, margin=0.3):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    g = np.asarray(im.convert('L'), float)
    small = g[::4, ::4]
    fg = small < otsu(small)
    # keep the largest blob roughly in the middle: drop rows/cols with only a few fg pixels (noise, vignetting)
    rows = np.nonzero(fg.sum(1) > 0.02 * fg.shape[1])[0]
    cols = np.nonzero(fg.sum(0) > 0.02 * fg.shape[0])[0]
    if len(rows) == 0 or len(cols) == 0:
        y0, y1, x0, x1 = 0, g.shape[0], 0, g.shape[1]
    else:
        y0, y1, x0, x1 = rows[0] * 4, rows[-1] * 4 + 4, cols[0] * 4, cols[-1] * 4 + 4
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
    H, W = g.shape
    side = min(max(y1 - y0, x1 - x0) * (1 + 2 * margin), H, W)
    # shift the square so it stays inside the photo (no padding: padded borders look like a second object)
    left = int(round(min(max(cx - side / 2, 0), W - side)))
    top = int(round(min(max(cy - side / 2, 0), H - side)))
    side = int(side)
    return im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)


def make_grid(pid):
    views = [ImageOps.expand(crop_photo(RC / SPLIT / 'images' / pid / 'rgb' / f'{k}.jpg'), border=3, fill='black')
             for k in (1, 2, 3, 4)]
    a = [np.array(v) for v in views]
    return Image.fromarray(np.vstack((np.hstack(a[:2]), np.hstack(a[2:]))))


def inputs(args):
    IN_DIR.mkdir(parents=True, exist_ok=True)
    for pid in ids(args.n):
        make_grid(pid).save(IN_DIR / f'{pid}.png')
    print(f'wrote {len(ids(args.n))} grids to {IN_DIR}')


# ------------------------------------------------------------------ generation
def gen(args):
    import torch
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate

    out = workdir(args.tag)
    (out / 'py').mkdir(parents=True, exist_ok=True)
    meta_path = out / 'gen_meta.jsonl'
    todo = [i for i in ids(args.n) if not (out / 'py' / f'{i}.py').exists()]
    print(f'{len(todo)} parts to generate', flush=True)
    if not todo:
        return
    dtype = getattr(torch, args.dtype)
    model = Cadrille.from_pretrained(str(Path(args.ckpt)), torch_dtype=dtype,
                                     attn_implementation='sdpa', device_map='cpu').eval()
    processor = AutoProcessor.from_pretrained(
        'Qwen/Qwen2-VL-2B-Instruct', min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28, padding_side='left')
    stop_ids = {processor.tokenizer.pad_token_id, processor.tokenizer.eos_token_id, 151645, 151643}
    t_all = time.time()
    for b in range(0, len(todo), args.bs):
        names = todo[b:b + args.bs]
        items = [{'video': [Image.open(IN_DIR / f'{n}.png').convert('RGB') if (IN_DIR / f'{n}.png').exists()
                            else make_grid(n)],
                  'description': 'Generate cadquery code', 'file_name': n} for n in names]
        batch = collate(items, processor=processor, n_points=256, eval=True)
        t = time.time()
        with torch.no_grad():
            gids = model.generate(
                input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                point_clouds=batch['point_clouds'], is_pc=batch['is_pc'], is_img=batch['is_img'],
                pixel_values_videos=batch['pixel_values_videos'].to(dtype),
                video_grid_thw=batch['video_grid_thw'], max_new_tokens=MAX_NEW_TOKENS)
        dt = time.time() - t
        gen_ids = gids[:, batch['input_ids'].shape[1]:]
        texts = processor.batch_decode(gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        with open(meta_path, 'a') as mf:
            for n, g, txt in zip(names, gen_ids, texts):
                ntok = int(sum(int(x) not in stop_ids for x in g))
                (out / 'py' / f'{n}.py').write_text(txt)
                mf.write(json.dumps({'id': n, 'n_tokens': ntok, 'hit_limit': ntok >= MAX_NEW_TOKENS,
                                     'batch_s': round(dt, 1), 'batch_size': len(names)}) + '\n')
        done = b + len(names)
        eta = (time.time() - t_all) / done * (len(todo) - done) / 60
        print(f'{args.tag} {done}/{len(todo)}  batch {dt:.0f}s  eta {eta:.0f} min', flush=True)


# ------------------------------------------------------------------ scoring
def rotations24():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3))
            for r, (c, s) in enumerate(zip(perm, signs)):
                R[r, c] = s
            if np.linalg.det(R) > 0:
                out.append(R)
    return out


def unit(m):
    m = m.copy()
    m.apply_translation(-(m.bounds[0] + m.bounds[1]) / 2)
    m.apply_scale(1.0 / m.extents.max())
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def _worker(tag, name, q):
    row = {'id': name, 'valid': False, 'iou_raw': None, 'cd_raw_x1000': None,
           'iou': None, 'cd_x1000': None, 'rot': None, 'error': ''}
    try:
        pm = be.py_to_mesh((workdir(tag) / 'py' / f'{name}.py').read_text())
        (workdir(tag) / 'mesh').mkdir(exist_ok=True)
        pm.export(workdir(tag) / 'mesh' / f'{name}_raw.stl')
        gt = be.load_unit(RC / SPLIT / 'meshes' / f'{name}.stl')
        pm = unit(pm)
        row['valid'] = True
        row['cd_raw_x1000'] = be.chamfer(gt, pm) * 1000
        best = None
        for k, R in enumerate(rotations24()):
            T = np.eye(4)
            T[:3, :3] = R
            cand = pm.copy()
            cand.apply_transform(T)
            cand = unit(cand)
            cd = be.chamfer(gt, cand)
            if best is None or cd < best[0]:
                best = (cd, k, cand)
        row['cd_x1000'], row['rot'] = best[0] * 1000, best[1]
        best[2].export(workdir(tag) / 'mesh' / f'{name}.stl')
        for key, m in (('iou_raw', pm), ('iou', best[2])):
            try:
                row[key] = float(be.iou(gt, m))
            except Exception as e:
                row['error'] += f'{key}: {type(e).__name__}: {str(e)[:80]} '
    except BaseException as e:
        row['error'] = f'{type(e).__name__}: {str(e)[:120]}'
    q.put(row)


def _score_one(tag, name):
    ctx = mp.get_context('spawn')
    q = ctx.Queue()
    p = ctx.Process(target=_worker, args=(tag, name, q))
    p.start()
    p.join(SCORE_TIMEOUT_S)
    if p.is_alive():
        p.terminate()
        p.join()
        return {'id': name, 'valid': False, 'error': 'timeout'}
    try:
        return q.get(timeout=5)
    except Exception:
        return {'id': name, 'valid': False, 'error': 'worker died'}


def score(args):
    out = workdir(args.tag)
    names = [n for n in ids(args.n) if (out / 'py' / f'{n}.py').exists()]
    meta = {}
    if (out / 'gen_meta.jsonl').exists():
        for line in (out / 'gen_meta.jsonl').read_text().splitlines():
            m = json.loads(line)
            meta[m['id']] = m
    with ThreadPoolExecutor(args.jobs) as ex:
        rows = list(ex.map(lambda n: _score_one(args.tag, n), names))
    for r in rows:
        r.update({k: meta.get(r['id'], {}).get(k) for k in ('n_tokens', 'hit_limit')})
    (out / 'scores.json').write_text(json.dumps(rows, indent=1))
    print(f'{args.tag}: scored {len(rows)}, valid {sum(r["valid"] for r in rows)}')


# ------------------------------------------------------------------ table
def _f(v, fmt='.1f', mul=1):
    return '-' if v is None else format(v * mul, fmt)


def table(args):
    names = ids(args.n)
    L = [f'# cadrille on RealCAD {SPLIT} (real photos, 4-view image input)', '',
         f'First {len(names)} parts of `data/realcad/{SPLIT}/ids.txt`. Photos cropped around the part and tiled '
         '2x2 (see `eval_realcad.py`). Prediction and GT normalised into the unit cube by bbox. '
         '"raw" = paper protocol; "aligned" = best of 24 axis-aligned rotations by Chamfer (shape up to rotation '
         '+ uniform scale). CD = Chamfer x1000 on 8192 points; IR = invalid programs. Greedy, 768 tokens, CPU.', '',
         '## Summary', '', '| metric | ' + ' | '.join(args.tags) + ' |', '|---|' + '---|' * len(args.tags)]
    per = {t: {r['id']: r for r in json.loads((workdir(t) / 'scores.json').read_text())} for t in args.tags}

    def col(t, k):
        return [per[t][i][k] for i in names if i in per[t] and per[t][i].get(k) is not None]
    stats = {}
    for t in args.tags:
        nv = sum(per[t].get(i, {}).get('valid', False) for i in names)
        stats[t] = {
            'parts': len(names), 'valid': nv, 'IR %': 100 * (len(names) - nv) / len(names),
            'mean IoU % aligned (valid)': 100 * np.mean(col(t, 'iou')) if col(t, 'iou') else None,
            'mean IoU % aligned (invalid = 0)': 100 * np.sum(col(t, 'iou')) / len(names) if col(t, 'iou') else None,
            'median IoU % aligned': 100 * np.median(col(t, 'iou')) if col(t, 'iou') else None,
            'median CD x1000 aligned': np.median(col(t, 'cd_x1000')) if col(t, 'cd_x1000') else None,
            'mean IoU % raw (valid)': 100 * np.mean(col(t, 'iou_raw')) if col(t, 'iou_raw') else None,
            'median CD x1000 raw': np.median(col(t, 'cd_raw_x1000')) if col(t, 'cd_raw_x1000') else None,
        }
    for k in stats[args.tags[0]]:
        L.append(f'| {k} | ' + ' | '.join(_f(stats[t][k], '.2f') if not isinstance(stats[t][k], int)
                                          else str(stats[t][k]) for t in args.tags) + ' |')
    L += ['', '## Per part', '', '| part | ' + ' | '.join(
        f'{t} valid | {t} IoU % (aligned) | {t} CD (aligned) | {t} IoU % (raw)' for t in args.tags) + ' |',
        '|---|' + '---|---|---|---|' * len(args.tags)]
    for i in names:
        cells = []
        for t in args.tags:
            r = per[t].get(i, {})
            cells += ['yes' if r.get('valid') else f'no ({r.get("error", "not run")[:30]})',
                      _f(r.get('iou'), mul=100), _f(r.get('cd_x1000'), '.3f'), _f(r.get('iou_raw'), mul=100)]
        L.append(f'| {i} | ' + ' | '.join(cells) + ' |')
    (HERE / 'results').mkdir(exist_ok=True)
    (HERE / 'results' / f'realcad_{SPLIT}.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (HERE / 'results' / f'realcad_{SPLIT}_summary.json').write_text(json.dumps(stats, indent=1, default=float))
    print('\n'.join(L))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['inputs', 'gen', 'score', 'table'])
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--ckpt', default=str(HERE / 'checkpoints' / 'cadrille-rl'))
    ap.add_argument('--tag', default='rl_dev')
    ap.add_argument('--tags', nargs='+', default=['rl_dev'])
    ap.add_argument('--bs', type=int, default=4)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--dtype', default='bfloat16', choices=['bfloat16', 'float32'])
    a = ap.parse_args()
    {'inputs': inputs, 'gen': gen, 'score': score, 'table': table}[a.mode](a)
