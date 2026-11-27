"""How are the ablation runs doing? Progress, problems, money, and what to rerun.

    uv run python check_runs.py                      # every runs/*_abl_* folder
    uv run python check_runs.py --watch 600          # repeat every 10 min
    uv run python check_runs.py --watch 600 --notify # + a macOS notification on changes
    uv run python check_runs.py --glob 'runs/*_pilot*' --parts data/fusion360/tuning.txt

Per config (a run folder plus its `_part2`, `_part3` ... folders) it prints
  * parts finished out of the expected list (--parts, default the 36 ablation parts)
  * its state: running (log.txt touched in the last --stale minutes), finished, paused
    (stopped cleanly with parts left, e.g. after a batch) or STOPPED (parts crashed/skipped)
  * parts skipped (first program did not build), crashed, or never started
  * Vertex retries seen (rate limits / dropped connections), and crashes
  * dollars spent so far (every logged round, finished or not) and the projected total
    from the mean cost of the finished parts; a warning when it passes --budget
and, for a stopped config with missing parts, the exact command to run them as `_partN`
(same flags, rebuilt from the run's config.json). Reads files only; never calls a model.
"""
import argparse
import json
import re
import shlex
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PART_RE = re.compile(r"^(?P<base>.+?)(?:_part(?P<n>\d+))?$")

# refine.py options that are worth repeating when they differ from refine.py's defaults
FLAGS = [  # (config key, default, how to write it)
    ("rounds", 4, lambda v: ["--rounds", str(v)]),
    ("budget_seconds", None, lambda v: ["--budget-seconds", str(v)]),
    ("repairs", 2, lambda v: ["--repairs", str(v)]),
    ("backend", "vertex", lambda v: ["--backend", v]),
    ("think", False, lambda v: ["--think"]),
    ("shadow_judge", False, lambda v: ["--shadow-judge"]),
    ("weights", True, lambda v: ["--no-weights"]),
    ("kernel", True, lambda v: ["--no-kernel"]),
    ("residuals", True, lambda v: ["--no-residuals"]),
    ("residual_images", True, lambda v: ["--no-residual-images"]),
    ("detail", True, lambda v: ["--no-detail"]),
    ("images", True, lambda v: ["--no-images"]),
    ("geo_signal", "both", lambda v: ["--geo-signal", v]),
    ("residual_view", "split", lambda v: ["--residual-view", v]),
    ("views", "all", lambda v: ["--views", v]),
    ("feedback", "image", lambda v: ["--feedback", v]),
    ("gate", "on", lambda v: ["--gate", v]),
    ("patience", 0, lambda v: ["--patience", str(v)]),
    ("sandbox", False, lambda v: ["--sandbox"]),
    ("seed", 0, lambda v: ["--seed", str(v)]),
]


def run_name(folder: Path) -> str:
    """'2026-11-27_abl_main_s1_part2' -> 'abl_main_s1_part2' (drops the date prefix)."""
    return re.sub(r"^\d{4}-\d{2}-\d{2}_", "", folder.name)


def read_jsonl(f: Path):
    rows = []
    for line in f.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:  # a line being written right now
            pass
    return rows


def part_state(run: Path, part: str, arms) -> tuple[str, int, int]:
    """-> (state, prompt tokens, output tokens) for one part in one run folder.
    state: done | skipped | started | absent."""
    d = run / "parts" / part
    if not d.exists():
        return "absent", 0, 0
    p = o = 0
    done = True
    for arm in arms:
        res = d / arm / "result.json"
        if res.exists():
            r = json.loads(res.read_text())
            p += r.get("prompt_tokens") or 0
            o += r.get("output_tokens") or 0
            continue
        done = False
        log = d / arm / "log.jsonl"
        if log.exists():  # unfinished or crashed: still count what was spent
            for row in read_jsonl(log):
                p += row.get("prompt_tokens") or 0
                o += row.get("output_tokens") or 0
    if done:
        return "done", p, o
    init = d / "init" / "internal" / "init.json"
    if init.exists() and not json.loads(init.read_text()).get("ok", True):
        return "skipped", p, o
    return "started", p, o


def rerun_command(cfg: dict, parts, name: str) -> str:
    known = cfg.get("targets", {})
    folder = str(Path(next(iter(known.values()))).parent) if known else "data/generated/targets"
    targets = [known.get(p, f"{folder}/{p}") for p in parts]  # same folder as the run's others
    cmd = ["caffeinate", "-i", "uv", "run", "python", "refine.py", *targets,
           "--arm", cfg.get("arm", "main")]
    if cfg.get("init"):
        cmd += ["--init", cfg["init"]]
    for key, default, write in FLAGS:
        if key in cfg and cfg[key] != default:
            cmd += write(cfg[key])
    return shlex.join(cmd + ["--name", name])


def check(args) -> tuple[list[str], dict]:
    """-> (report lines, {config: status}) for the run folders matching args.glob."""
    expected = [l.strip() for l in args.parts.read_text().splitlines() if l.strip()]
    groups = defaultdict(list)
    for f in sorted(ROOT.glob(args.glob)):
        if f.is_dir() and (f / "config.json").exists():
            m = PART_RE.match(run_name(f))
            groups[m["base"]].append(f)
    if not groups:
        return [f"no run folders match {args.glob}"], {}
    out, total_spent, total_proj, status = [], 0.0, 0.0, {}
    head = (f"{'config':22s} {'done':>7s} {'state':8s} {'skip':>4s} {'crash':>5s} "
            f"{'retry':>5s} {'spent':>7s} {'$/part':>7s} {'proj.':>7s}  note")
    out += [head, "-" * len(head)]
    todo = []
    for base, runs in sorted(groups.items()):
        cfgs = [json.loads((r / "config.json").read_text()) for r in runs]
        arms = cfgs[0].get("arms") or [cfgs[0].get("arm")]
        price = cfgs[0].get("prices") or {}
        pin, pout = price.get("input_per_m", 0), price.get("output_per_m", 0)
        rank = {"done": 3, "started": 2, "skipped": 1, "absent": 0}
        best = {p: ("absent", 0.0, 0.0) for p in expected}  # part -> (state, $, mtime)
        spent, retries = 0.0, 0
        newest = 0.0
        for r in runs:
            log = r / "log.txt"
            if log.exists():
                retries += log.read_text(errors="replace").count("[vertex]")
                newest = max(newest, log.stat().st_mtime)
            for p in expected:
                st, pt, ot = part_state(r, p, arms)
                usd = pt / 1e6 * pin + ot / 1e6 * pout
                spent += usd
                if rank[st] > rank[best[p][0]]:   # done beats in progress beats skipped
                    d = r / "parts" / p
                    mtime = max((f.stat().st_mtime for f in d.rglob("*")), default=0.0) \
                        if st == "started" else 0.0
                    best[p] = (st, usd, mtime)
        done = [p for p in expected if best[p][0] == "done"]
        skipped = [p for p in expected if best[p][0] == "skipped"]
        started = sorted((p for p in expected if best[p][0] == "started"),
                         key=lambda p: best[p][2])     # oldest activity first
        absent = [p for p in expected if best[p][0] == "absent"]
        running = time.time() - newest < args.stale * 60
        crashed = started[:-1] if running else started   # the newest one may still be running
        state = ("finished" if len(done) == len(expected) else "running" if running
                 else "STOPPED" if crashed or skipped else "paused")  # paused: a batch ended cleanly
        per_part = sum(best[p][1] for p in done) / len(done) if done else 0.0
        proj = spent + per_part * (len(expected) - len(done)) if done else 0.0
        note = []
        if running and started:
            note.append(f"working on {started[-1]}")
        if done and proj > args.budget:
            note.append(f"OVER BUDGET: projected ${proj:.0f} > ${args.budget:.0f}")
        if retries >= args.retry_warn:
            note.append("many retries: run fewer configs in parallel")
        out.append(f"{base:22s} {len(done):3d}/{len(expected):<3d} {state:8s} {len(skipped):4d} "
                   f"{len(crashed):5d} {retries:5d} {spent:7.2f} {per_part:7.2f} "
                   f"{proj:7.2f}  {'; '.join(note)}")
        status[base] = {"state": state, "over": bool(done and proj > args.budget),
                        "retries": retries >= args.retry_warn, "done": len(done),
                        "proj": proj, "missing": len(skipped) + len(crashed)}
        total_spent += spent
        total_proj += proj if done else spent
        missing = skipped + crashed + ([] if running else absent)
        if missing and not running:
            n = max(int(PART_RE.match(run_name(r))["n"] or 1) for r in runs) + 1
            todo.append((base, missing, rerun_command(cfgs[0], missing, f"{base}_part{n}")))
    out.append("-" * len(head))
    out.append(f"{'total':22s} {'':7s} {'':8s} {'':4s} {'':5s} {'':5s} {total_spent:7.2f} "
               f"{'':7s} {total_proj:7.2f}")
    for base, missing, cmd in todo:
        out += ["", f"{base}: {len(missing)} part(s) to rerun: {' '.join(missing)}", f"  {cmd}"]
    return out, status


def alerts(prev: dict, cur: dict) -> list[str]:
    """What changed for the worse (or finished) since the last check. On the first check
    (prev empty) only problems are reported."""
    msgs = []
    for base, s in cur.items():
        p = prev.get(base, {})
        if s["state"] != p.get("state") and s["state"] in ("STOPPED", "paused", "finished") \
                and (p or s["state"] == "STOPPED"):
            what = {"STOPPED": f"stopped with {s['missing']} part(s) crashed or skipped",
                    "paused": f"batch done ({s['done']} parts), nothing broken",
                    "finished": "finished"}[s["state"]]
            msgs.append(f"{base}: {what}")
        if s["over"] and not p.get("over"):
            msgs.append(f"{base}: projected ${s['proj']:.0f}, over budget")
        if s["retries"] and not p.get("retries"):
            msgs.append(f"{base}: many Vertex retries (rate limits or network)")
    return msgs


def notify(msgs: list[str]) -> None:
    """macOS desktop notification (silently skipped elsewhere)."""
    import subprocess
    text = "; ".join(msgs)[:240].replace('"', "'")
    subprocess.run(["osascript", "-e", f'display notification "{text}" with title '
                    f'"Ablation runs" sound name "Glass"'], check=False,
                   capture_output=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--glob", default="runs/*_abl_*", help="run folders to check")
    ap.add_argument("--parts", type=Path, default=ROOT / "data/fusion360/ablation.txt",
                    help="the parts every config should cover")
    ap.add_argument("--budget", type=float, default=20.0,
                    help="warn when a config's projected cost passes this many dollars")
    ap.add_argument("--stale", type=float, default=15.0,
                    help="minutes without a log update before a run counts as stopped")
    ap.add_argument("--retry-warn", type=int, default=10,
                    help="warn when a config has seen this many Vertex retries")
    ap.add_argument("--watch", type=float, default=None, metavar="SECONDS",
                    help="repeat every SECONDS")
    ap.add_argument("--notify", action="store_true",
                    help="macOS notification when a config stops, pauses, finishes, goes over "
                         "budget or sees many retries (use with --watch)")
    args = ap.parse_args(argv)
    prev = {}
    while True:
        lines, status = check(args)
        print(time.strftime("%Y-%m-%d %H:%M"), "\n" + "\n".join(lines), flush=True)
        msgs = alerts(prev, status)
        if msgs:
            print("ALERT: " + "; ".join(msgs), flush=True)
            if args.notify:
                notify(msgs)
        prev = status
        if not args.watch:
            break
        time.sleep(args.watch)
        print()


if __name__ == "__main__":
    main()
