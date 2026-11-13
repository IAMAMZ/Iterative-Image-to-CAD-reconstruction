"""Run cadrille (4-view image mode, CPU) over the Fusion360 test split and score every instance.

  python eval_fusion360.py gen   --ckpt checkpoints/cadrille-rl --tag rl  [--bs 8] [--limit N]
  python eval_fusion360.py score --tag rl [--jobs 8]
  python eval_fusion360.py table --tags rl sft            # -> results/fusion360_test.{csv,md}

Input : data/raw/fusion360_test_mesh/<part>.stl for the parts in data/splits/fusion360_test.txt
Gen   : batched, resumable; one predicted CadQuery program per part -> work_dirs/f360_<tag>/py/<part>.py
Score : paper protocol (evaluate.py): the prediction is normalised by its own bbox (centre 0.5, longest side
        1), the GT likewise; volumetric IoU by mesh booleans (manifold3d); Chamfer distance on 8192 points.
        Each part is scored in its own process with a timeout; a program that errors, times out or gives an
        empty mesh is "invalid" (counts towards IR).
"""
import argparse
import csv
import json
import multiprocessing as mp
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import batch_eval as be

HERE = Path(__file__).parent
DATA = HERE.parent / 'data'
SRC = DATA / 'raw' / 'fusion360_test_mesh'
MAX_NEW_TOKENS = 768
SCORE_TIMEOUT_S = 120


def test_ids(limit=None):
    ids = [l.strip() for l in (DATA / 'splits' / 'fusion360_test.txt').read_text().split() if l.strip()]
    return ids[:limit]


def workdir(tag):
    return HERE / 'work_dirs' / f'f360_{tag}'


# ------------------------------------------------------------------ generation
def gen(args):
    import torch
    from transformers import AutoProcessor
    from cadrille import Cadrille, collate
    from run_one import make_grid

    out = workdir(args.tag)
    (out / 'py').mkdir(parents=True, exist_ok=True)
    meta_path = out / 'gen_meta.jsonl'
    todo = [i for i in test_ids(args.limit) if not (out / 'py' / f'{i}.py').exists()]
    print(f'{len(todo)} parts to generate', flush=True)
    if not todo:
        return
    dtype = getattr(torch, args.dtype)
    model = Cadrille.from_pretrained(str(HERE / args.ckpt), torch_dtype=dtype,
                                     attn_implementation='sdpa', device_map='cpu').eval()
    processor = AutoProcessor.from_pretrained(
        'Qwen/Qwen2-VL-2B-Instruct', min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28,
        padding_side='left')
    stop_ids = {processor.tokenizer.pad_token_id, processor.tokenizer.eos_token_id, 151645, 151643}
    t_all = time.time()
    for b in range(0, len(todo), args.bs):
        names = todo[b:b + args.bs]
        items = [{'video': [make_grid(be.load_unit(SRC / f'{n}.stl'))],
                  'description': 'Generate cadquery code', 'file_name': n} for n in names]
        batch = collate(items, processor=processor, n_points=256, eval=True)
        t = time.time()
        with torch.no_grad():
            ids = model.generate(
                input_ids=batch['input_ids'], attention_mask=batch['attention_mask'],
                point_clouds=batch['point_clouds'], is_pc=batch['is_pc'], is_img=batch['is_img'],
                pixel_values_videos=batch['pixel_values_videos'].to(dtype),
                video_grid_thw=batch['video_grid_thw'], max_new_tokens=MAX_NEW_TOKENS)
        dt = time.time() - t
        n_in = batch['input_ids'].shape[1]
        gen_ids = ids[:, n_in:]
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
def _worker(tag, name, q):
    import trimesh
    row = {'id': name, 'valid': False, 'iou': None, 'cd_x1000': None, 'error': ''}
    try:
        t = time.time()
        pm = be.py_to_mesh((workdir(tag) / 'py' / f'{name}.py').read_text())
        row['exec_s'] = round(time.time() - t, 1)
        (workdir(tag) / 'mesh').mkdir(exist_ok=True)
        pm.export(workdir(tag) / 'mesh' / f'{name}_raw.stl')
        c = (pm.bounds[0] + pm.bounds[1]) / 2
        pm.apply_translation(-c)
        pm.apply_scale(1.0 / pm.extents.max())
        pm.apply_translation([0.5, 0.5, 0.5])
        pm.export(workdir(tag) / 'mesh' / f'{name}.stl')
        gt = be.load_unit(SRC / f'{name}.stl')
        row['valid'] = True
        row['cd_x1000'] = be.chamfer(gt, pm) * 1000
        try:
            row['iou'] = float(be.iou(gt, pm))
        except Exception as e:
            row['error'] = f'iou: {type(e).__name__}: {str(e)[:100]}'
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
        return {'id': name, 'valid': False, 'iou': None, 'cd_x1000': None, 'error': 'timeout'}
    try:
        return q.get(timeout=5)
    except Exception:
        return {'id': name, 'valid': False, 'iou': None, 'cd_x1000': None, 'error': 'worker died'}


def score(args):
    out = workdir(args.tag)
    names = [n for n in test_ids(args.limit) if (out / 'py' / f'{n}.py').exists()]
    meta = {}
    if (out / 'gen_meta.jsonl').exists():
        for line in (out / 'gen_meta.jsonl').read_text().splitlines():
            m = json.loads(line)
            meta[m['id']] = m
    with ThreadPoolExecutor(args.jobs) as ex:
        rows = []
        for i, r in enumerate(ex.map(lambda n: _score_one(args.tag, n), names), 1):
            r.update({k: meta.get(r['id'], {}).get(k) for k in ('n_tokens', 'hit_limit')})
            rows.append(r)
            if i % 20 == 0:
                print(f'scored {i}/{len(names)}', flush=True)
    (out / 'scores.json').write_text(json.dumps(rows, indent=1))
    print(f'{args.tag}: scored {len(rows)}, valid {sum(r["valid"] for r in rows)}')


# ------------------------------------------------------------------ table
def _stats(rows, n_total):
    valid = [r for r in rows if r['valid']]
    ious = [r['iou'] for r in rows if r['iou'] is not None]
    cds = [r['cd_x1000'] for r in rows if r['cd_x1000'] is not None]
    return {
        'n': n_total, 'valid': len(valid), 'IR_%': 100.0 * (n_total - len(valid)) / n_total,
        'iou_scored': len(ious),
        'mean_IoU_valid_%': 100 * float(np.mean(ious)) if ious else None,
        'mean_IoU_invalid_as_0_%': 100 * float(np.sum(ious)) / n_total if ious else None,
        'median_IoU_%': 100 * float(np.median(ious)) if ious else None,
        'p10_IoU_%': 100 * float(np.percentile(ious, 10)) if ious else None,
        'median_CD_x1000': float(np.median(cds)) if cds else None,
        'mean_CD_x1000': float(np.mean(cds)) if cds else None,
        'hit_token_limit_%': 100.0 * sum(bool(r.get('hit_limit')) for r in rows) / n_total,
        'mean_tokens': float(np.mean([r['n_tokens'] for r in rows if r.get('n_tokens') is not None] or [0])),
    }


def table(args):
    ids = test_ids(args.limit)
    per = {}
    for tag in args.tags:
        rows = json.loads((workdir(tag) / 'scores.json').read_text())
        per[tag] = {r['id']: r for r in rows}
    Path(HERE / 'results').mkdir(exist_ok=True)
    cols = ['id'] + [f'{t}_{c}' for t in args.tags for c in ('valid', 'iou_%', 'cd_x1000', 'n_tokens', 'error')]
    with open(HERE / 'results' / 'fusion360_test.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for i in ids:
            row = [i]
            for t in args.tags:
                r = per[t].get(i)
                if r is None:
                    row += ['', '', '', '', 'not run']
                else:
                    row += [int(r['valid']), '' if r['iou'] is None else round(100 * r['iou'], 2),
                            '' if r['cd_x1000'] is None else round(r['cd_x1000'], 4),
                            r.get('n_tokens', ''), r.get('error', '')]
            w.writerow(row)
    stats = {t: _stats([per[t][i] for i in ids if i in per[t]], len(ids)) for t in args.tags}
    paper = {'sft': (0.20, 77.6, 3.2), 'rl': (0.17, 84.6, 0.0)}
    L = ['# cadrille on Fusion360 test (4-view image input)', '',
         f'{len(ids)} parts from `data/splits/fusion360_test.txt` (our seeded 20% of the 1725 Fusion360 test meshes). '
         'Protocol follows cadrille `evaluate.py`: prediction and GT both normalised into the unit cube by bbox; '
         'IoU = volumetric (mesh booleans); CD = Chamfer distance on 8192 points, median, x1000; '
         'IR = share of programs that give no valid mesh. One sample per part (greedy, max 768 new tokens), '
         'run on CPU (bf16, sdpa attention).', '', '## Summary', '']
    keys = [('n', 'parts'), ('valid', 'valid programs'), ('IR_%', 'IR %'),
            ('mean_IoU_valid_%', 'mean IoU % (valid only)'), ('mean_IoU_invalid_as_0_%', 'mean IoU % (invalid = 0)'),
            ('median_IoU_%', 'median IoU %'), ('p10_IoU_%', '10th-percentile IoU %'),
            ('median_CD_x1000', 'median CD x1000'), ('mean_CD_x1000', 'mean CD x1000'),
            ('hit_token_limit_%', 'hit 768-token limit %'), ('mean_tokens', 'mean generated tokens')]
    L.append('| metric | ' + ' | '.join(args.tags) + ' |')
    L.append('|---|' + '---|' * len(args.tags))
    for k, label in keys:
        vals = []
        for t in args.tags:
            v = stats[t][k]
            vals.append('-' if v is None else (str(v) if isinstance(v, int) else f'{v:.2f}'))
        L.append(f'| {label} | ' + ' | '.join(vals) + ' |')
    L += ['', 'Paper, Fusion360 multi-view images (Table 2): SFT (Rpi) CD 0.20 / IoU 77.6 / IR 3.2; '
          'RL (Dr. CPPO) CD 0.17 / IoU 84.6 / IR 0.0. The paper evaluates all 1725 parts; this is a 345-part subset.',
          '', '## Per instance', '', '| part | ' + ' | '.join(f'{t} valid | {t} IoU % | {t} CD x1000' for t in args.tags) + ' |',
          '|---|' + '---|---|---|' * len(args.tags)]
    for i in ids:
        cells = []
        for t in args.tags:
            r = per[t].get(i)
            if r is None:
                cells += ['-', '-', '-']
            else:
                cells += ['yes' if r['valid'] else f'no ({r.get("error", "")[:30]})',
                          '-' if r['iou'] is None else f'{100 * r["iou"]:.1f}',
                          '-' if r['cd_x1000'] is None else f'{r["cd_x1000"]:.3f}']
        L.append(f'| {i} | ' + ' | '.join(cells) + ' |')
    (HERE / 'results' / 'fusion360_test.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    (HERE / 'results' / 'fusion360_test_summary.json').write_text(json.dumps(stats, indent=1))
    print('\n'.join(L[:30]))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['gen', 'score', 'table'])
    ap.add_argument('--ckpt', default='checkpoints/cadrille-rl')
    ap.add_argument('--tag', default='rl')
    ap.add_argument('--tags', nargs='+', default=['rl', 'sft'])
    ap.add_argument('--bs', type=int, default=8)
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--dtype', default='bfloat16', choices=['bfloat16', 'float32'])
    a = ap.parse_args()
    {'gen': gen, 'score': score, 'table': table}[a.mode](a)
