"""Re-score existing RealCAD predictions with the RealCAD paper's Chamfer convention (no regeneration).

  python score_realcad_cd.py --tag rl_dev --n 20 [--seeds 5]   (other splits: REALCAD_SPLIT=test50 python ...)

Convention, from github.com/sunyh39/RealCAD (dataset/json2pc.py, cadlib/extrude.py, evaluation/evaluate_ae_cd.py):
  GT    : cad_seq.normalize() -> uniform scale about the ORIGIN (no centring) so that max|bbox coord| = 0.75,
          bbox = cad_json properties.bounding_box (NORM_FACTOR = 0.75)
  points: 2000 surface samples per shape (trimesh.sample_surface)
  CD    : mean(d_gt->pred^2) + mean(d_pred->gt^2), squared, no multiplier; median over valid parts
Our predictions have no shared frame with the GT (real photos), so the prediction is placed in the GT's normalised
frame by matching bbox centre and longest side (uniform scale): "raw" = as generated, "aligned" = best of the 24
axis-aligned rotations by this CD. Each CD is averaged over --seeds point samplings.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

from eval_realcad import RC, SPLIT, ids, rotations24, workdir

N_POINTS = 2000
NORM_FACTOR = 0.75


def gt_mesh(pid):
    rel = next(l.strip() for l in (RC / SPLIT / 'ids.txt').read_text().split() if l.strip().endswith(pid))
    bb = json.loads((RC / 'cad_json' / f'{rel}.json').read_text())['properties']['bounding_box']
    box = np.array([[bb['max_point'][k] for k in 'xyz'], [bb['min_point'][k] for k in 'xyz']])
    m = trimesh.load(RC / SPLIT / 'meshes' / f'{pid}.stl')
    m.apply_scale(NORM_FACTOR / np.abs(box).max())
    return m


def place_like(pred, gt):
    p = pred.copy()
    p.apply_translation(-(p.bounds[0] + p.bounds[1]) / 2)
    p.apply_scale(gt.extents.max() / p.extents.max())
    p.apply_translation((gt.bounds[0] + gt.bounds[1]) / 2)
    return p


def cd(gt, pred, seed):
    np.random.seed(seed)  # trimesh.sample_surface uses np.random
    a, _ = trimesh.sample.sample_surface(gt, N_POINTS)
    b, _ = trimesh.sample.sample_surface(pred, N_POINTS)
    d1, _ = cKDTree(b).query(a)
    d2, _ = cKDTree(a).query(b)
    return float(np.mean(d1 ** 2) + np.mean(d2 ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='rl_dev')
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--seeds', type=int, default=5)
    a = ap.parse_args()
    out = workdir(a.tag)
    rows = []
    for pid in ids(a.n):
        raw = out / 'mesh' / f'{pid}_raw.stl'
        if not raw.exists():
            rows.append({'id': pid, 'valid': False})
            continue
        gt, pred = gt_mesh(pid), trimesh.load(raw)
        mean_cd = lambda p: float(np.mean([cd(gt, p, s) for s in range(a.seeds)]))
        r_raw = mean_cd(place_like(pred, gt))
        best = min(rotations24(), key=lambda R: cd(gt, place_like(pred.copy().apply_transform(
            np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]])), gt), 0))
        T = np.eye(4)
        T[:3, :3] = best
        r_al = mean_cd(place_like(pred.copy().apply_transform(T), gt))
        rows.append({'id': pid, 'valid': True, 'cd_raw': r_raw, 'cd_aligned': r_al,
                     'gt_max_extent': float(gt.extents.max())})
        print(f'{pid}  raw {r_raw:.4f}  aligned {r_al:.4f}', flush=True)
    v = [r for r in rows if r['valid']]
    summary = {'n': len(rows), 'valid': len(v), 'IR_%': 100 * (len(rows) - len(v)) / len(rows),
               'mCD_raw': float(np.median([r['cd_raw'] for r in v])),
               'mCD_aligned': float(np.median([r['cd_aligned'] for r in v])),
               'mean_CD_raw': float(np.mean([r['cd_raw'] for r in v])),
               'mean_CD_aligned': float(np.mean([r['cd_aligned'] for r in v]))}
    (out / 'scores_realcad_cd.json').write_text(json.dumps({'summary': summary, 'rows': rows}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
