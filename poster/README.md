# Poster draft

`poster.tex` is the poster for the Dec 2 session (LaTeX, `tikzposter`, A0 landscape).
`poster.pdf` is the current build. Grey dashed boxes are placeholders; each names the
workstream in [`docs/PLAN.md`](../docs/PLAN.md) that fills it.

## Build

```sh
cd poster && tectonic poster.tex          # brew install tectonic; or upload this folder to Overleaf
```

The four columns are tight. After any edit, rebuild and check that nothing runs off the
bottom of a column. Shorten text before shrinking fonts.

## Layout

The layout follows the meeting with the professor:
1. **Headline:** does the harness make a cheap model (Gemini 3.8 Flash) beat the same model
   without it, and a frontier model in one shot, per dollar?
2. **Real photos** (RealCAD) next.
3. The synthetic noise study is kept only to **explain** the real-photo gap.

Columns: idea + setup | loop, methods, checker example | results | real photos + discussion.
Everything follows PR #11: 4 table views, union-based capped depth error, edit feedback,
patience.

## What is real and what is a placeholder

| Block | Content | Status | Filled by |
|---|---|---|---|
| The idea, inverse problem, data/start/metrics | text, formulas | real | n/a |
| The refinement loop | diagram (with the feedback arrow) + methods table | real; frontier model name `[model]` pending | pick the model |
| What the checker sees | `figures/checker_example.png` (4-view rig) | real | `make_example_figure.py` |
| Does the harness pay off: price vs. performance | placeholder | pending (headline) | W1 + W8 → `figures/pareto.png` |
| Paired gain over cadrille | placeholder | pending | W1 + W8 (noise floor = `main` vs `main_s1`) |
| Who judges edits better | placeholder | pending | W1 `--shadow-judge` |
| Making the loop learn: example | text | illustrative; replace with a real attempt log | W2 |
| Making the loop learn: 3D IoU vs. round | placeholder | pending | W2 |
| Real photos (RealCAD) | placeholder; cadrille 35% is real (`cadrille/results/realcad_dev.md`) | pending | W6 |
| Why real photos are hard: table + callout | Stage 2 numbers (PR #9) | real, but **8-view rig and old score**; rerun on 4 views | Stage 2 rerun |
| Measured SAM 3 bias | placeholder | pending | W6 |
| Discussion: headline | `\pending{...}` | pending | W1 |

Dropped after the meeting: the "no LLM / open model" box (W4, W5) and the noise-tolerant rule
box (W3, only if a real bias is found).

## Figures

- `checker_example.png` comes from `uv run python poster/make_example_figure.py`. It renders
  cadrille's program with a free echo dry run of `refine.py` (no model calls), then composes
  target / program / silhouette residual / depth error for part `61899_93eee6e5_0000` in the
  views `top_front` and `top_right`. It needs 4-view targets (rebuild with
  `data/fusion360_targets.py --force` if `--targets` still holds the old 8-view renders).
  `--part`, `--views`, `--targets` and `--run` pick another example.

## Before printing

- [ ] Confirm the required poster size (A0 landscape here; for 48×36 in, change the
      `\documentclass` paper options).
- [ ] Replace every placeholder, or delete it if its workstream did not finish by Nov 29 (G2).
- [ ] Remove the "DRAFT" note from `\institute`.
- [ ] Every number traces to `docs/results/` or `docs/STAGE2.md`.
- [ ] Stage 2 table rerun on the 4-view rig with the new score, and the `\pending` note removed.
