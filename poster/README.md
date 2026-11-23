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

## What is real and what is a placeholder

| Block | Content | Status | Filled by |
|---|---|---|---|
| The question, inverse problem, setup | text, formulas | real | n/a |
| The refinement loop | diagram + arm table | real | n/a |
| What the checker sees | `figures/checker_example.png` | real | `make_example_figure.py` |
| Stage 1: 3D IoU gain per arm | placeholder | pending | W1 + W8 → `figures/stage1_gain_by_arm.png` |
| Stage 1: who judges edits better | placeholder | pending | W1 + W8 → `figures/stage1_judge_vs_gate.png` |
| Stage 1: no LLM, open model | placeholder | pending | W5, W4 → small table |
| Making the loop learn: history example | text | illustrative; replace with a real one from the W2 logs | W2 |
| Making the loop learn: 3D IoU vs. round | placeholder | pending | W2 → `figures/w2_iou_by_round.png` |
| Stage 2: accuracy chart + table + insight | `figures/stage2_checker_accuracy.png` | real (PR #9) | n/a |
| Stage 2: noise-tolerant rule | placeholder | pending | W3 → `figures/stage2_robust_rule.png` |
| Real photos | placeholder | pending | W6 → `figures/realcad_noise.png` |
| Takeaways item 4 | `\pending{...}` | pending | W1 |

## Figures

- `checker_example.png` comes from `uv run python poster/make_example_figure.py`. It renders
  cadrille's program with a free echo dry run of `refine.py` (no model calls), then composes
  target / program / silhouette residual / depth error for part `61899_93eee6e5_0000`.
  `--part` and `--views` pick another example.
- `stage2_*.png` are copies of `docs/figures/` from PR #9 (`checker_eval.py`). **Before
  printing**, regenerate them with larger fonts. At A0 their labels are too small.

## Before printing

- [ ] Confirm the required poster size (A0 landscape here; for 48×36 in, change the
      `\documentclass` paper options).
- [ ] Replace every placeholder, or delete it if its workstream did not finish by Nov 29 (G2).
- [ ] Remove the "DRAFT" note from `\institute`.
- [ ] Every number traces to `docs/results/` or `docs/STAGE2.md`.
