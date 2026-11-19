# cadrille on RealCAD dev (real photos, 4-view image input)

First 20 parts of `data/realcad/dev/ids.txt`. Photos cropped around the part and tiled 2x2 (see `eval_realcad.py`). Prediction and GT normalised into the unit cube by bbox. "raw" = paper protocol; "aligned" = best of 24 axis-aligned rotations by Chamfer (shape up to rotation + uniform scale). CD = Chamfer x1000 on 8192 points; IR = invalid programs. Greedy, 768 tokens, CPU.

## Summary

| metric | rl_dev |
|---|---|
| parts | 20 |
| valid | 20 |
| IR % | 0.00 |
| mean IoU % aligned (valid) | 34.99 |
| mean IoU % aligned (invalid = 0) | 34.99 |
| median IoU % aligned | 35.69 |
| median CD x1000 aligned | 21.27 |
| mean IoU % raw (valid) | 26.67 |
| median CD x1000 raw | 44.66 |

## Per part

| part | rl_dev valid | rl_dev IoU % (aligned) | rl_dev CD (aligned) | rl_dev IoU % (raw) |
|---|---|---|---|---|
| 00010860 | yes | 3.0 | 52.715 | 4.6 |
| 00014933 | yes | 1.9 | 70.996 | 1.9 |
| 00015721 | yes | 59.5 | 14.837 | 35.6 |
| 00016984 | yes | 51.4 | 14.538 | 27.2 |
| 00017301 | yes | 36.4 | 20.867 | 13.8 |
| 00017346 | yes | 23.8 | 31.964 | 23.8 |
| 00020425 | yes | 35.0 | 13.922 | 18.7 |
| 00059365 | yes | 26.7 | 28.320 | 10.0 |
| 00075947 | yes | 42.0 | 45.286 | 42.0 |
| 00081067 | yes | 31.9 | 66.997 | 31.4 |
| 00081530 | yes | 41.9 | 41.908 | 31.4 |
| 00110304 | yes | 41.5 | 11.355 | 41.0 |
| 00120803 | yes | 14.4 | 26.316 | 1.4 |
| 00124489 | yes | 67.3 | 10.955 | 59.5 |
| 00143853 | yes | 20.6 | 19.076 | 8.4 |
| 00144212 | yes | 54.7 | 6.175 | 54.7 |
| 00144967 | yes | 48.9 | 21.607 | 47.2 |
| 00146110 | yes | 34.5 | 18.192 | 17.5 |
| 00147363 | yes | 5.7 | 22.416 | 4.5 |
| 00147439 | yes | 58.9 | 20.928 | 58.9 |
