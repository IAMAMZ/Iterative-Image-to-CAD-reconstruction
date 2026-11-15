# Upstream

Vendored copy of https://github.com/col14m/cadrille at commit d72acc6 ("Update README.md").
Upstream files are unchanged. Added by us:

- `run_one.py`   - run cadrille (image mode, CPU) on one mesh; inputs rendered with open3d like `dataset.py`
- `batch_eval.py` - generate on several dev meshes (`gen`) and score IoU / Chamfer / invalid (`score`) with the paper's protocol

Weights are not tracked: download `maksimko123/cadrille` and `maksimko123/cadrille-rl` from Hugging Face into
`cadrille/checkpoints/cadrille` and `cadrille/checkpoints/cadrille-rl`.

On Windows set `KMP_DUPLICATE_LIB_OK=TRUE` (torch and OpenBLAS both ship an OpenMP runtime).
