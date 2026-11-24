# Our work on top of CADCodeVerify and GATOR

We refine a CadQuery program, starting from cadrille's prediction, until its renders match
images of a target part. The loop comes from **GATOR**: start from an initial model, edit, render,
review, keep or revert. The verification and repair ideas, and most of our baselines, come from
**CADCodeVerify**. What we add replaces the agent's own judgement in both: a ground-truth-free
**geometric checker** with **view weights**, and **CAD-kernel diagnostics**.

Arm names below are the ones in `refine.py` (`ARMS`). `geo` is the main method; `hybrid` is an
ablation.

## At a glance

| | CADCodeVerify | GATOR | Ours |
|---|---|---|---|
| Input | Text prompt | 1+ casual photos | Target images (renders now; noisy masks/depth/photos next) |
| Output | CadQuery program | Textured mesh + scene pose | CadQuery program |
| Starting point | Model writes from scratch | Generated asset | cadrille's program + placement fit |
| What the agent sees | 4 renders (0/90/180/270°) | Renders under matched cameras | Target vs current renders, red/blue overlays, depth-error maps, zoom on the largest residual, per-view table |
| Who decides an edit is kept | Every edit is kept | Agent compares renders | Geometric checker (masks + depth, view-weighted) |
| Error feedback | Compiler errors after a failed build | None (meshes have no CAD kernel) | Per-operation kernel errors and warnings, also after a successful build |
| Training | None | Large generative model on ~980k assets | None |

## CADCodeVerify

*Generating CAD Code with Vision-Language Models for 3D Designs*, ICLR 2025.

### What it introduces
1. A visual refinement loop: the model inspects renders of its own CadQuery output and fixes the code.
2. Verification by 2–5 Yes/No questions generated from the text prompt, answered on 4 renders with
   reasoning; "Unclear" is allowed, and Yes answers are dropped from the feedback.
3. Feedback in natural language, so a text-only code model can use it.
4. A repair loop that feeds compiler errors back before verification.
5. The CADPrompt benchmark (200 objects, text prompts, expert CadQuery code).
6. Comparisons against 3D-Premise and a geometric solver that sees the true shape.

### What we match
| Their piece | Our version | Where |
|---|---|---|
| Question generation, answering, feedback | Reimplemented; questions come from the target images instead of a text prompt | `vlm.QUESTIONS_PROMPT`, `ANSWER_PROMPT`, `FEEDBACK_PROMPT` |
| "Unclear" answers, Yes answers dropped | Kept as-is | `vlm.parse_answers`, `vlm.qa_text` |
| Their method as a baseline | `vlm` arm (questions + feedback; edits kept by an A/B model judge) | `refine.py` |
| 3D-Premise baseline | `premise` arm (images + A/B judge, no questions) | `refine.py` |
| Geometric-solver upper bound | `gsolver` arm (sees the true shape; analysis only) | `refine.py` |
| CadQuery as the CAD language | Adopted | — |
| Compiler-error repair loop | Kept, up to `--repairs` retries (default 2) | `refine.Agent.write_program` |
| Compile rate next to shape metrics | Reported | `eval3d.py`, `report.py` |

Our `vlm` arm differs in one respect: CADCodeVerify keeps every edit, while ours reverts edits the
judge rejects, so all arms share GATOR's keep-or-revert loop. `gsolver` keeps every edit, as they do.

### What we improve
- **Measured instead of asked.** CADCodeVerify claims its questions match the geometric solver
  without seeing the true shape. Our `geo` arm also never sees the true shape, but measures the
  mismatch per view (silhouette IoU, missing/extra pixels, depth error) instead of asking the model
  about it. The headline comparison is `geo` vs `vlm`, with `gsolver` as the ceiling.
- **The questions' failure mode.** When every answer is Yes, the question loop has nothing to fix
  and stops. On pilot5 this ended `hybrid` runs after round 1 while the geometry still showed
  errors. `hybrid` (our checker + their questions) tests whether their review adds anything on top
  of the checker; on pilot5 it did not (mean 3D IoU 0.726 → 0.762, vs 0.832 for `geo`, 8 parts).
- **Kernel diagnostics, not just compile errors.** Their loop only acts on a failed build. Ours
  traces every CadQuery operation, names the one that failed with a hint, and also reports edits
  that built but did nothing (`no_effect`) or split the part into pieces (`op_checker.py`).

### What we ignore
- **The CADPrompt benchmark.** Our input is images of a part, not a description. We use Fusion360
  (Stage 1) and RealCAD (real photos).
- **Feedback for text-only code models.** We always use a model that can see images.

## GATOR

### What it introduces
1. **Local modality mixing** in a structure → geometry → appearance diffusion cascade: RGB, mask and
   depth-pointmap tokens are fused per patch before cross-view attention, so noisy depth or masks
   can be cross-checked. Also a silhouette + depth rendering step that refines translation and scale.
2. **Text conditioning at every stage** of the cascade (category names and captions).
3. **Agentic refinement starting from the generated asset**: an agent with Blender edits the mesh in
   an edit–render–review loop under matched cameras, keeps verified improvements, reverts
   regressions, works within a time budget, and preserves the asset's frame and scale.
4. **S3**, a synthetic data pipeline of ~980k assets in cluttered scenes with occluded and
   estimator-perturbed observations, and evaluation on real captures with noisy cameras, depth
   and masks.

### What we match
| Their piece | Our version | Where |
|---|---|---|
| Start from an initial model as a scaffold | cadrille's program is round 0 | `cadrille_init.py convert` |
| Fit scale by rendering silhouettes and depth | Placement fit: isotropic scale in [0.7, 1.4], grid + golden-section search on the geo score (not differentiable) | `cadrille_init.py convert` |
| Edit–render–review loop, matched cameras | Same 8 cameras for target and candidate | `refine.py`, `rig.py` |
| Keep improvements, revert regressions | Every arm except `gsolver` | `refine.py` |
| Time budget | `--rounds` and `--budget-seconds` | `refine.py` |
| Preserve frame and scale | Rules in the system prompt | `vlm.SYSTEM` |
| Zoomed detail view | Crop of the largest missing/extra region: target, current, overlay | `refine.detail_strip` |
| Noisy masks, depth and cameras | Planned robustness test; RealCAD test50 has SAM 3 masks and VGGT cameras and depth | `data/realcad/test50` |

### What we improve
- **Editable CAD instead of a mesh.** GATOR's output is a mesh; ours stays a parametric CadQuery
  program.
- **The review is measured.** In GATOR the agent judges its own edits from renders. Our geometric
  checker decides from silhouettes and depth: an edit is kept only if the view-weighted score
  (`geo_check.geo_score`) rises by more than 0.001 and no trusted view loses more than 0.05 IoU.
- **Cross-checking views without training.** GATOR learns to cross-check noisy masks and depth
  inside its network. `view_weights.py` does it with geometry alone: each target view's depth is
  projected into the other views, and views the others contradict get a lower weight, so one bad
  view cannot block a good edit.
- **Kernel feedback.** A mesh has no CAD kernel, so GATOR has no equivalent of our per-operation
  diagnostics.

### What we ignore
- **Training a generator** (modality mixing, the diffusion cascade, Plücker rays). cadrille
  produces our starting program.
- **Text conditioning.** We have no text input.
- **S3 training data.** We use its idea (perturbed observations) as a test condition, not as
  training data.
- **Scene composition, texture, UVs, placement recall and physics stability.** We reconstruct one
  part's shape; we score 3D IoU, Chamfer distance and compile rate (`eval3d.py`).

## Our contributions

1. **GT-free geometric checker** (`compare.py`, `geo_check.py`): per-view silhouette IoU, missing
   and extra pixels, and depth error; it tells the agent what to fix and decides whether the edit
   is kept.
2. **View weights** (`view_weights.py`): trust per target view from cross-view consistency. On clean
   renders every weight is 1.0, so they only matter once masks and depth are noisy.
3. **CAD-kernel diagnostics** (`op_checker.py`, `vlm.kernel_report`): errors and warnings per
   CadQuery operation, with hints, both when the build fails and when it succeeds. On pilot5, 4 of
   24 edits needed a repair (all then built) and 3 had kernel warnings.
4. **Local open-weight model as the agent.** Listed in `PIPELINE.md`, but every run so far used
   Gemini through Vertex AI. Keep it only once a local-model run exists; otherwise reword it as a
   local vs Gemini comparison.

## Evidence so far

Pilot5, 9 tuning parts (Gemini, before the prompt clean-up), mean 3D IoU over the 8 parts that ran
both arms:

| Arm | Start | Final |
|---|---|---|
| `geo` (main method) | 0.726 | 0.832 |
| `hybrid` (ablation: geo + CADCodeVerify questions) | 0.726 | 0.762 |

Not yet run against each other: `geo` vs `vlm` (CADCodeVerify-style) vs `premise` (3D-Premise), with
`gsolver` and `oracle` as ceilings.
