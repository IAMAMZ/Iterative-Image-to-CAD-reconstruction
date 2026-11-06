# Iterative Image-to-CAD Reconstruction

Write a 3D part as code, then take pictures of it from fixed angles.

## Scripts

- `examples/flange.py` — a 3D part written as CadQuery code (just the shape, nothing else).
- `generate_solid.py` — runs a part file, checks the part is OK, saves it, and takes its pictures.
- `cq_render.py` — the camera: turns a 3D shape into pictures.
- `rig.py` — decides where the 8 cameras stand; saves them in `rig.json`.

## Setup

```sh
uv sync                     # or: conda env create -f environment.yml
```

## Run

```sh
uv run python generate_solid.py examples/flange.py
```

Pictures and files appear in `out/flange/`.

## Make your own part

Copy `examples/flange.py`, change the shape, and keep the last line as `result = ...`.
