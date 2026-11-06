# Iterative Image-to-CAD Reconstruction

Write a 3D part as code, then take pictures of it from fixed angles.

## Scripts

- `examples/flange.py` — a 3D part written as CadQuery code (just the shape, nothing else).
- `generate_solid.py` — runs a part file, checks the part is OK, saves it, and takes its pictures.
- `op_checker.py` — watches every CadQuery command as it runs and logs the illegal ones (with the line and a hint how to fix it).
- `cq_render.py` — the camera: turns a 3D shape into pictures.
- `rig.py` — decides where the 8 cameras stand; saves them in `rig.json`.
- `part_generators.py` — makes random simple parts (plates, brackets, stepped blocks) as part files.
- `compare.py` — scores a guess against the real 3D part: how well outlines overlap (IoU) and how far off the depth is, per camera.
- `compare_image.py` — scores a guess against just a picture of the part (no 3D model): finds the camera angle, then compares outlines.

## Setup

```sh
uv sync                     # or: conda env create -f environment.yml
```

## Run

```sh
uv run python generate_solid.py examples/flange.py
```

Pictures and files appear in `out/flange/`.

Every command is checked by the CAD kernel and written to `out/flange/ops_log.jsonl`.
If a command is illegal the run stops, exits with code 1, and prints e.g.

```
[ERROR  ] step  6 (line 3) fillet(20): StdFail_NotDone: BRep_API: command not done
          hint: the fillet/chamfer is too big for the selected edges ...
```

## Test

```sh
uv run pytest tests -v -s
```

- `tests/test_illegal_shapes.py` — sends illegal commands and checks each is caught, at the right step, with a hint.
- `tests/test_part_generators.py` — checks every random part is a real, correct shape.
- `tests/test_compare.py` — checks the scores and colours of the checker are right.
- `tests/test_compare_image.py` — checks the picture checker finds the right angle and scores wrong parts lower.

## Make many random parts

```sh
uv run python part_generators.py --n 10      # 10 of each kind → out/parts/
```

## Make your own part

Copy `examples/flange.py`, change the shape, and keep the last line as `result = ...`.

## Compare a guess to the real part

```sh
uv run python generate_solid.py real.py  --out out/real
uv run python generate_solid.py guess.py --out out/guess --like out/real   # same size frame!
uv run python compare.py out/real out/guess
```

Look at `out/guess/compare/summary.png`: red = material the guess is missing,
blue = extra material, the heatmap = how wrong the depth is (pale = right, dark = wrong).

## Compare a guess to just a picture

At test time there is no 3D model, only an image. This finds the camera angle
that best fits, lines the outlines up, and scores how well they match.

```sh
uv run python generate_solid.py guess.py --out out/guess
uv run python compare_image.py photo.png out/guess                  # camera unknown: search
uv run python compare_image.py photo.png out/guess --camera iso_fr  # camera known
```

Look at `out/guess/compare_image/summary.png`: the picture, the guess from the found
angle, and the overlay (red = missing, blue = extra). Size can't be judged from one
picture, so only the shape counts.
