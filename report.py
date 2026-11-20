"""Human-facing pages of a refine.py run, rewritten after every part so a run can be read
while it is still going.

    runs/<date>_<name>/
      README.md            start here: status, headline table, where to look, terms
      results.md           every part x arm: start vs final 3D IoU (worst start first)
      results/             parts.csv  edits.csv  summary.json  figures/*.png
      config.json          the exact refine.py settings (+ target paths)
      log.txt              console output of the run
      parts/<part>/
        progress.png       start → round 1 → round 2 ... per arm, one view, + 3D IoU chart
        compare.png        detail: target | start | each arm's final; 4 views + depth error
        scores.md          round-by-round table per arm (the model's CHANGE line, kept?)
        questions.json     verification questions (question arms only)
        init/              the shared starting program (rendered-solid folder, layout.py)
        <arm>/
          final            -> the round the arm ended with (or ../init)
          round_01_kept/   program.py solid.stl conversation.json renders/ diff/ internal/
          round_02_rejected/ ...   (suffix: kept|rejected|failed|no-change|stopped)
          log.jsonl  result.json
        internal/          view_weights.json

    uv run python report.py runs/<run>       # rebuild the pages of an existing run
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import layout
import progress
from summarize_runs import load, summarize

VIEWS = ("front", "right", "top", "iso_fr")
ARM_TEXT = {
    "premise": "renders only; the VLM judge decides (3D-Premise-style baseline)",
    "vlm": "renders + failed verification questions; the VLM judge decides (CADCodeVerify-style)",
    "geo": "main method (ours): renders + silhouette/depth residuals; the geometric check decides",
    "hybrid": "ablation: geo + CADCodeVerify-style questions and judge; check AND judge must agree",
    "oracle": "as geo, but kept only if the hidden 3D IoU goes up (analysis upper bound)",
    "gsolver": "as vlm + GT geometric properties, every edit kept (CADCodeVerify geometric solver*)",
}


class Tee:
    """Copy everything printed to stdout into a log file while the context is open."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.f = open(self.path, "a", buffering=1)
        self.stdout, sys.stdout = sys.stdout, self
        return self

    def write(self, s):
        self.stdout.write(s)
        self.f.write(s)

    def flush(self):
        self.stdout.flush()
        self.f.flush()

    def __exit__(self, *exc):
        sys.stdout = self.stdout
        self.f.close()


# ------------------------------------------------------------------ helpers
def _f(x, p=3):
    return "–" if x is None else f"{x:.{p}f}"


def _delta(a, b):
    if a is None or b is None:
        return ""
    return f" ({b - a:+.3f})"


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _tile(path, label, tile):
    if path is not None and Path(path).exists():
        im = Image.open(path).convert("RGB").resize((tile, tile), Image.LANCZOS)
    else:
        im = Image.new("RGB", (tile, tile), (235, 235, 235))
    d = ImageDraw.Draw(im)
    d.rectangle(d.textbbox((5, 4), label), fill=(255, 255, 255))   # readable on dark tiles
    d.text((5, 4), label, fill=(0, 0, 0))
    return im


def start_label(cfg):
    init = str(cfg.get("init") or "")
    return "start (cadrille)" if "cadrille" in init else "start" if init else "start (agent)"


# ------------------------------------------------------------------ per part
def compare_png(part_dir: Path, target: Path | None, columns, out: Path, tile=200, head=24):
    """columns: [(label, rendered-solid dir)]. Rows: the 4 renders, then 4 depth-error maps
    (the target column shows its own depth map there)."""
    cols = [("target", target)] + columns
    sheet = Image.new("RGB", (tile * len(cols), head + 2 * len(VIEWS) * tile), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (lab, src) in enumerate(cols):
        d.text((i * tile + 6, 6), lab, fill=(0, 0, 0))
        for j, v in enumerate(VIEWS):
            p = None if src is None else layout.render(src, v)
            sheet.paste(_tile(p, v, tile), (i * tile, head + j * tile))
            if src is None:
                p = None
            elif i == 0:
                p = layout.render(src, v, "_depth")
            else:
                p = layout.diff(src, v, "_depth_err")
            sheet.paste(_tile(p, f"{v} {'depth' if i == 0 else 'depth error'}", tile),
                        (i * tile, head + (len(VIEWS) + j) * tile))
    sheet.save(out)


def scores_md(part, part_dir, target, arms, rows, finals, init_iou, cfg):
    lines = [f"# {part}", "", "![progress, round by round](progress.png)", "",
             "Detail of the final programs in four views: [compare.png](compare.png) (top four "
             "rows renders, bottom four depth error against the target; pale = right depth, "
             "red = material missing, blue = extra).", ""]
    if target is not None:
        gt = target / "gt.stl" if (target / "gt.stl").exists() else target / "solid.stl"
        lines += [f"Target: `{target}` · ground-truth mesh: `{gt}`", ""]
    lines += [f"{start_label(cfg).capitalize()}: 3D IoU **{_f(init_iou)}** · `init/program.py`", "",
              "| arm | 3D IoU start → final | silhouette IoU | rounds | stop | final program |",
              "|---|---|---|---|---|---|"]
    for a in arms:
        fin = finals.get((part, a))
        if fin is None:
            lines.append(f"| {a} | (running) | | | | |")
            continue
        lines.append(f"| {a} | {_f(init_iou)} → **{_f(fin.get('iou3d'))}**"
                     f"{_delta(init_iou, fin.get('iou3d'))} | {_f(fin.get('w_iou'))} | "
                     f"{fin.get('rounds_run')} | {fin.get('stop')} | `{a}/final/program.py` |")
    for a in arms:
        rs = sorted((r for r in rows if r["part"] == part and r["arm"] == a and r["round"] > 0),
                    key=lambda r: r["round"])
        lines += ["", f"## {a}", "", ARM_TEXT.get(a, ""), ""]
        if not rs:
            lines.append("No rounds logged yet.")
            continue
        lines += ["| round | folder | change (model's words) | 3D IoU before → after | "
                  "silhouette IoU | check | judge | questions Yes |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in rs:
            change = r.get("change") or r.get("stop") or r.get("status")
            if r.get("change_tag") and r.get("change_tag") not in ("no_change",):
                change = f"[{r['change_tag']}] {change}"
            check = "" if r.get("geo_decision") is None else \
                ("pass" if r["geo_decision"] else "fail") + \
                (" (inconclusive)" if r.get("geo_inconclusive") else "")
            judge = "" if r.get("vlm_decision") is None else "keep" if r["vlm_decision"] else "drop"
            qa = "" if r.get("qa_n") is None else f"{r.get('qa_yes')}/{r['qa_n']}"
            iou = "" if r.get("status") != "ok" else \
                f"{_f(r.get('iou3d_before'))} → {_f(r.get('iou3d'))} ({r.get('verdict')})"
            folder = f"`{a}/{r['dir']}`" if r.get("dir") else ""
            lines.append(f"| {r['round']} | {folder} | {_cell(change)[:220]} | {iou} | "
                         f"{_f(r.get('w_iou'))} | {check} | {judge} | {qa} |")
    (part_dir / "scores.md").write_text("\n".join(lines) + "\n")


# ------------------------------------------------------------------ run pages
def arm_table(summary, arms):
    lines = ["| arm | parts | 3D IoU start → final (median) | mean | improved / worse | "
             "invalid edits | kept edits that helped | tokens / part | min / part |",
             "|---|---|---|---|---|---|---|---|---|"]
    for arm in [a for a in arms if a in summary]:
        m = summary[arm]
        q = m["quality"]["iou3d"]
        mi = lambda d, k="median": None if d is None else d[k]
        acc = m["acceptance"]
        helped = "–" if not acc["n"] else \
            f"{acc['counts'].get('kept-good', 0)} / {sum(v for k, v in acc['counts'].items() if k.startswith('kept'))}"
        wall = m.get("wall_seconds_per_part")
        lines.append(
            f"| {arm} | {m['parts']} | {_f(mi(q['init']))} → **{_f(mi(q['final']))}** | "
            f"{_f(mi(q['init'], 'mean'))} → {_f(mi(q['final'], 'mean'))} | "
            f"{m['parts_improved']} / {m['parts_worse']} | {_f(m['invalid_rate'], 2)} | {helped} | "
            f"{_f(m['tokens_per_part'], 0)} | {_f(None if wall is None else wall / 60, 1)} |")
    return lines


def results_md(root, cfg, summary, parts, arms, init_iou, finals):
    lines = [f"# Results: {root.name}", "",
             "3D IoU against the hidden ground-truth shape (1 = identical). The agent never "
             "sees it; it is the offline score.", "", "## Per arm", "", *arm_table(summary, arms),
             "", "*kept edits that helped*: kept edits that raised 3D IoU / all kept edits.", "",
             "## Progress by part", "",
             "![3D IoU by round, per part](results/figures/progress_by_part.png)", "",
             "## Per part", "", "Worst starting program first. Δ = final − start.", "",
             "| part | start | " + " | ".join(arms) + " | pictures |",
             "|---|---|" + "---|" * len(arms) + "---|"]
    for p in sorted(parts, key=lambda p: (init_iou.get(p) is None, init_iou.get(p) or 0)):
        cells = []
        for a in arms:
            fin = finals.get((p, a))
            cells.append("–" if fin is None else
                         f"{_f(fin.get('iou3d'))}{_delta(init_iou.get(p), fin.get('iou3d'))} "
                         f"· {fin.get('stop')}")
        lines.append(f"| [{p}](parts/{p}/scores.md) | {_f(init_iou.get(p))} | "
                     + " | ".join(cells) + f" | [progress](parts/{p}/progress.png) · [detail](parts/{p}/compare.png) |")
    figs = sorted(f for f in (root / "results" / "figures").glob("*.png")
                  if f.name != "progress_by_part.png")
    if figs:
        lines += ["", "## Figures", ""]
        lines += [f"![{f.stem}](results/figures/{f.name})" for f in figs]
    lines += ["", "## Machine-readable", "",
              "- `results/parts.csv`: one row per part and arm (final scores, tokens, time)",
              "- `results/edits.csv`: one row per edit (decision of the gate, shadow decisions, "
              "what it did to 3D IoU)",
              "- `results/summary.json`: everything in the tables above and more "
              "(see `summarize_runs.py`)"]
    (root / "results.md").write_text("\n".join(lines) + "\n")


def readme_md(root, cfg, summary, parts, arms, finals, finished):
    n = cfg.get("n_targets", len(parts))
    done = sum(all((p, a) in finals for a in arms) for p in parts)
    status = "finished" if finished else f"running ({done} of {n} parts done)"
    ex = sorted(parts)[0] if parts else "<part>"
    lines = [
        f"# Run {root.name}", "",
        f"**{status}** · started {cfg.get('started', '?')} · {n} part{'s' * (n != 1)} · arms "
        f"{', '.join(arms)} · up to {cfg.get('rounds')} rounds · {cfg.get('backend')} / "
        f"`{cfg.get('model')}` · starting programs: `{cfg.get('init') or 'written by the agent'}`",
        "", "## Headline", "", *(arm_table(summary, arms) if summary else ["(no part finished yet)"]),
        "", "## Start here", "",
        "1. **[results.md](results.md)**: every part with its start and final 3D IoU per arm, "
        "worst starting program first, linked to the part's pages.",
        "2. **[results/figures/progress_by_part.png](results/figures/progress_by_part.png)**: "
        "one small chart per part, 3D IoU of the kept program round by round, every arm.",
        f"3. **`parts/<part>/progress.png`** (e.g. [{ex}](parts/{ex}/progress.png)): the target, "
        "then per arm the program after every round (shape over depth error, in the view where "
        "the start was most wrong), framed green = kept, red = rejected, with its 3D IoU. "
        "`compare.png` next to it is the detailed version (4 views, final programs only).",
        "4. **`parts/<part>/scores.md`**: round by round, what the model said it changed, "
        "whether the arm kept it, and what it did to 3D IoU.",
        "5. **`parts/<part>/<arm>/final/`**: the program the arm ended with (`program.py`) and its "
        "mesh (`solid.stl`). Open it next to the target's `gt.stl` (path in scores.md) in a "
        "mesh viewer (f3d, MeshLab).",
        "", "## Folder layout", "", "```",
        f"{root.name}/",
        "  README.md  results.md     you are here / the full tables",
        "  results/                  parts.csv  edits.csv  summary.json  figures/",
        "  config.json  log.txt      exact settings / console output",
        "  parts/",
        f"    {ex}/",
        "      progress.png  compare.png  scores.md",
        "      questions.json        verification questions (question arms)",
        "      init/                 the starting program every arm edits",
        f"      {arms[0] if arms else '<arm>'}/",
        "        final -> round_NN_kept   (or ../init when nothing was kept)",
        "        round_01_kept/      program.py  solid.stl  conversation.json",
        "                            renders/  diff/  internal/",
        "        round_02_rejected/  ...",
        "        log.jsonl  result.json",
        "```", "",
        "Inside every program folder (`init/`, `round_*`): `program.py` (CadQuery), "
        "`solid.stl` / `solid.step` (the built shape), `conversation.json` (prompt, the model's "
        "replies and repairs, the gate's decision), `renders/` (8 cameras: shaded, mask, depth), "
        "`diff/` (vs the target: `<view>_overlay.png`, `<view>_depth_err.png`, `summary.png`, "
        "`report.json`), `internal/` (info.json, depth.npz, CAD-kernel ops log).", "",
        "## Terms", "",
        "- **3D IoU** (`iou3d`): volume overlap with the hidden ground truth; offline score only.",
        "- **silhouette IoU** (`w_iou`): view-weighted 2D outline overlap over the 8 cameras; "
        "what the geometric check sees. It is blind to depth-only errors (an offset hidden "
        "inside the outline), so check the depth-error rows too.",
        "- **round folder suffix**: `kept` (edit accepted), `rejected` (built, but the arm's gate "
        "said no), `failed` (did not build after the repairs), `no-change` (model said nothing "
        "to fix), `stopped` (every verification question answered Yes).",
        "- **stop**: `rounds` (ran out of rounds), `no_change`, `all_questions_yes`, `budget`.",
        "- **arms** in this run:",
        *[f"  - `{a}`: {ARM_TEXT.get(a, '')}" for a in arms],
        "", "Rebuild these pages: `uv run python report.py " + str(root) + "`"]
    (root / "README.md").write_text("\n".join(lines) + "\n")


def write(root: Path, finished=False):
    root = Path(root)
    cfg_f = root / "config.json"
    cfg = json.loads(cfg_f.read_text()) if cfg_f.exists() else {}
    rows, finals = load(root)
    summary = summarize(root) if rows else {}
    (root / "results").mkdir(exist_ok=True)
    (root / "results" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    try:
        from figures import write_figures
        write_figures(root)
    except Exception as e:  # noqa: BLE001 - pages must not fail on a plot
        print(f"  (figures skipped: {type(e).__name__}: {e})")
    arms = cfg.get("arms") or sorted({a for _, a in finals})
    targets = {k: Path(v) for k, v in (cfg.get("targets") or {}).items()}
    parts = sorted(p.name for p in (root / "parts").iterdir() if p.is_dir()) \
        if (root / "parts").is_dir() else []
    init_iou = {r["part"]: r.get("iou3d") for r in rows if r["round"] == 0}
    for p in parts:
        part_dir = root / "parts" / p
        if not layout.is_rendered(part_dir / "init"):
            continue                      # starting program did not build: nothing to show
        cols = [(f"{start_label(cfg)} {_f(init_iou.get(p))}", part_dir / "init")]
        for a in arms:
            fin = finals.get((p, a))
            if fin is not None:
                cols.append((f"{a} {_f(fin.get('iou3d'))}", part_dir / a / "final"))
        target = targets.get(p)
        compare_png(part_dir, target if target and target.exists() else None, cols,
                    part_dir / "compare.png")
        scores_md(p, part_dir, target, arms, rows, finals, init_iou.get(p), cfg)
    try:
        progress.write(root, cfg, start_label(cfg))
    except Exception as e:  # noqa: BLE001
        print(f"  (progress figures skipped: {type(e).__name__}: {e})")
    results_md(root, cfg, summary, parts, arms, init_iou, finals)
    readme_md(root, cfg, summary, parts, arms, finals, finished)


def main():
    ap = argparse.ArgumentParser(description="rebuild README.md / results.md / per-part pages")
    ap.add_argument("root", type=Path, help="a refine.py run folder")
    args = ap.parse_args()
    write(args.root, finished=True)
    print(f"wrote {args.root / 'README.md'}")


if __name__ == "__main__":
    main()
