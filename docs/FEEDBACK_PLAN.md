# Plan: edit feedback in the refine loop

## 1. Problem

Each round is a fresh, stateless request (`Agent.write_program` builds `messages` from
`SYSTEM` + one `refine_prompt`). When the checker rejects an edit, the current state does not
change. The next round therefore gets **the same prompt and the same images** as the round
before. The agent cannot learn three things:

- that it already tried something,
- that the attempt was rejected,
- why it was rejected: which view got worse, by how much, and whether the cause was missing or
  extra material, or depth.

At temperature 1.0 it gets a fresh sample of the same distribution, so it often proposes the
same edit again. Pilot 5 (`runs/2026-11-17_pilot5_relayout`, geo arm) already shows this:

| part | round 1 (rejected) | round 2 (rejected) |
|---|---|---|
| `56065_00bbe5da_0003` | "increase ring thickness from 27 to 27.5" | "increase extrusion depth from 27 to 27.5" |
| `24195_9791f5d3_0005` | "add the symmetric counterbores ... inner hole radius to 83.5" | "add symmetric counterbores ... inner hole diameter to 84" |
| `21604_520e1ae2_0001` | "move the through-holes outward from ±83 to ±85" | "... holes at ±83.25 ..." (same direction, smaller step) |

Each repeat costs a full round of the budget and learns nothing new.

## 2. Idea

After every edit, tell the agent what that edit did, measured by the same GT-free checker that
decided it. The next prompt then includes three things:

1. **what it tried**: its own CHANGE line and the code diff;
2. **what happened**: kept / rejected / failed to build, and the rule that decided;
3. **where and by how much**: the per-view change in IoU, missing px, extra px and depth error,
   plus an image of the pixels the edit fixed and the pixels it broke.

Nothing in the feedback uses the GT mesh or `eval3d`. It only restates the checker's numbers,
so the method stays GT-free.

## 3. What the feedback contains

### 3.1 Attempt log (text, always on when feedback is on)

The log has one entry per attempt **since the last kept edit**. It is reset when an edit is
kept, because the state the attempts referred to is gone. It is capped at the last 3 attempts
to bound tokens. Example:

```
Previous attempts from this same program (all rejected; the program below is unchanged):

Attempt 1 (round 3) — you said: "dimensional — increase ring thickness from 27 to 27.5"
  diff:   - .extrude(27)
          + .extrude(27.5)
  result: REJECTED — geometric score fell by 0.004 (needs a gain > 0.001)
  view       IoU            missing px     extra px      depth err
  top_front  0.912 → 0.905  1210 → 1190    310 → 520     0.031 → 0.034
  top_right  0.884 → 0.871  ...
  worst: top_right IoU −0.013, mostly EXTRA material (blue) along the top edge
  → The part got taller where the target is not. Do not repeat this change; consider the
    opposite direction or a different feature.
```

A short **round history** comes after the log. It has one line per earlier round, including
kept rounds (`round 1 kept +0.021 "fix cylinder centre"`), so the agent sees the whole path.

Entries per outcome:

| outcome | what the entry says |
|---|---|
| rejected (gain ≤ `min_gain`) | score delta, per-view table, worst view |
| rejected (view guard) | "overall score rose by X but trusted view V lost Y IoU (limit 0.05)": a local win that broke another view |
| rejected (inconclusive) | "changed the score by less than 0.001: the edit had almost no visible effect" (often a no-op or a hidden feature) |
| rejected (judge, `hybrid`) | the judge's last reasoning paragraph |
| failed to build | the final build error after repairs, short form from `op_checker` |
| kept | one line in the round history: delta and the most-improved view |

### 3.2 Edit-effect image (optional, image variant)

For the rejected candidate, each view of the 4-view grid is coloured **relative to the current
state**:

- **green**: was wrong, now right (the edit fixed these pixels);
- **red**: was right, now wrong (the edit broke these pixels);
- grey: correct before and after;
- faint: wrong before and after.

This answers "where in this image did it fail" directly. The existing overlay shows only the
state of one candidate against the target, so it can't show what an edit changed. The image is
built from the three masks (target, current, rejected). The depth version would use the same
colours on `|Δdepth|`. Only the latest rejected attempt gets an image, which keeps the image
count to +1 per prompt.

### 3.3 Repeat guard (cheap, always on when feedback is on)

Before building, the guard normalises the proposed program (strip comments and whitespace,
round number literals to 3 significant digits) and compares it with every attempt since the
last kept edit. If it matches one, the program is not built or scored. The agent gets back:
"this is the same program as attempt N, which was rejected because ...; propose a different
change". This uses one repair slot. Every such hit is logged as `repeat_blocked`.

## 4. Stateless summary, not a growing chat

The alternative is to keep one multi-turn conversation per part. That carries every earlier
image (4–5 per round), so tokens grow with the square of the round count. It also mixes old
residual images with current ones, and makes "what the agent saw" hard to control or ablate.
The plan keeps each round stateless and adds a **structured feedback block** to
`refine_prompt`, with bounded size and the same position in every prompt. The multi-turn
version is a possible later variant, but it is not part of this plan.

## 5. Interaction with the other ablations (`docs/ABLATION_PLAN.md`)

- **`--gate off`:** nothing is rejected, but the feedback still states the effect of the last
  edit ("your last edit lowered the score by X in view V"). With the gate off, feedback is the
  only signal that an edit went wrong.
- **`--patience K`:** tentative edits are reported as "kept tentatively, score below the last
  committed state by X". A rollback is reported as "rolled back to round N; the branch
  (attempts ...) never beat it".
- **`--geo-signal mask|depth`:** the feedback uses only the columns and images of the active
  signal, so the ablation stays clean.
- **`--views worst`:** the feedback covers only that view.
- **`premise` / `vlm` arms:** the judge's verdict and reasoning only, no geometric numbers.

## 6. Implementation

1. **`geo_check.geo_accept`** returns a `reason` (`gain`, `view_drop`, `inconclusive`, `kept`)
   alongside `details`. New `edit_delta(cur_report, new_report, weights)` returns per-view
   Δ IoU / missing / extra / depth_err, the worst view, and whether the change was mostly
   missing or mostly extra.
2. **`compare.py`:** `edit_effect_image(mask_t, mask_cur, mask_new)` (and the depth version),
   written to `<round>/diff/<view>_effect.png`; plus a grid helper in `refine.py`.
3. **`refine.py`:**
   - `attempts` list per arm, reset on keep. Each entry holds round, CHANGE tag/text, unified
     diff vs the current program (`difflib`, capped at ~30 lines), decision, reason, delta,
     and the build error.
   - `history` list of one-liners for all rounds.
   - Repeat guard inside `write_program` (normalise + compare before `build`).
   - `--feedback {none,text,image}` (default `none` until the feedback pilot picks the
     variant, then that variant; `image` includes `text`). Recorded in `config.json`.
4. **`vlm.py`:** `feedback_block(attempts, history, signal)` and the image-number bookkeeping
   in `refine_prompt` (the effect image becomes the last image). The `SYSTEM` prompt gets one
   rule: "If previous attempts are listed, do not repeat a rejected change; use what they show
   about direction and size."
5. **`echo` backend:** it must parse prompts that contain the feedback block. Optionally, it
   could react by perturbing a different number than the rejected attempt did, to exercise the
   path in tests.
6. **Logging / reports:** `log.jsonl` gets `feedback_attempts`, `repeat_blocked` and
   `reject_reason`. `summarize_runs.py` gets the metrics in §7. `scores.md` shows the reject
   reason.
7. **Tests:**
   - a rejected edit puts the attempt in the next prompt;
   - a kept edit resets the log;
   - a repeated program is blocked without a build;
   - the cap of 3 attempts holds;
   - the reasons are classified correctly in `geo_accept`;
   - on a synthetic mask triple, the effect image's colours are correct;
   - no `eval3d` field ever appears in a prompt (a GT-leak test).

## 7. How to measure it

New metrics in `summarize_runs.py`, which also apply to existing runs:

- **repeat rate:** the share of proposals whose program (normalised) or CHANGE line is
  near-identical to an earlier rejected attempt from the same state (difflib ratio ≥ 0.9 on the
  program). First compute it on pilot 5 and the coming baseline runs to show the size of the
  problem.
- acceptance rate, rounds to the first kept edit, and the share of rounds that end on the same
  program;
- kept-precision and harmful-accept rate (feedback must not make the agent game the checker);
- final and `best_geo` 3D IoU, tokens and $ per part (the feedback costs tokens).

**Decided (2026-11-24): feedback joins the main method before the ablation run.** The
feedback pilot on the 9 tuning parts compares three configs:

| id | change |
|---|---|
| `fb_none` | today's `geo` method (`--feedback none`) |
| `fb_text` | `--feedback text` (attempt log + history + repeat guard) |
| `fb_image` | `--feedback image` (+ edit-effect image) |

The winner of `fb_text` / `fb_image` becomes the default and part of `main`. In the ablation
grid (`ABLATION_PLAN.md`, group G), feedback then appears as removals: `no_feedback`, and
`fb_text_only` if the image variant wins.

## 8. Order of work

1. Compute the repeat rate on existing runs (no model calls), to measure the problem.
2. Implement §6 with echo tests.
3. Pilot `fb_none`, `fb_text` and `fb_image` on the **9 tuning parts** only. Read a few
   prompts by hand to check that the block is clear and correct. Report, then wait for
   go-ahead.
4. Make the winning variant the default `--feedback` and freeze its prompt text. Only then do
   the ablation flags and pilot in `ABLATION_PLAN.md` §4 start, so that every ablation is
   measured on the final method.

## 9. Risks

- **Prompt length.** A 3-attempt cap and capped diffs keep the block to about 1–2k tokens.
  The effect image adds 1 image.
- **Over-correction.** "Do not repeat" may push the agent away from a right change that
  failed only because its size was wrong. The text says "consider a different size or
  direction", not "abandon this feature".
- **Gaming the checker.** With exact numbers, the agent may make small edits that improve the
  silhouette without fixing the shape. Watch for this in kept-precision and in the gap between
  `best_geo` and the 3D IoU.
