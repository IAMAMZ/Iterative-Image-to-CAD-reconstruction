#!/usr/bin/env bash
# Runbook B (docs/ABLATION_RUN_B.md), started in the background so a closed terminal or a
# logged-out shell doesn't stop it. The configs are split over LANES lanes; each lane runs its
# configs one after another, so at most LANES runs call Gemini at the same time.
#
#   bash run_b.sh              # the 6 required configs, 3 lanes
#   LANES=2 bash run_b.sh      # gentler on the machine and on Vertex
#   bash run_b.sh secondary    # no_detail, no_kernel, signed_resid
#   DRY=1 bash run_b.sh        # print each lane's commands (targets left out), start nothing
#
# Staged (recommended): every config on 6 parts first (one per stratum), check cost and
# behaviour with check_runs.py, then the other 30 as _part2 (check_runs.py merges them):
#   PARTS=data/fusion360/ablation_batch1.txt bash run_b.sh
#   PARTS=data/fusion360/ablation_batch2.txt SUFFIX=_part2 bash run_b.sh
# Test knobs (for a cheap end-to-end check, not for real runs):
#   LIMIT=2 EXTRA="--backend echo --rounds 1" PREFIX=smoke- bash run_b.sh
#   LIMIT = first N parts only; EXTRA = flags appended last (they win); PREFIX = run-name
#   prefix, so test folders never match check_runs.py's runs/*_abl_* glob.
#
# Progress:  uv run python check_runs.py          (or --watch 600)
# Logs:      logs/run_b_lane<N>.log
# Stop all:  pkill -f "refine.py.*--name abl_"
# Keep the charger in: caffeinate keeps the Mac awake only while it has power.
set -euo pipefail
cd "$(dirname "$0")"

T=()
while IFS= read -r p; do [ -n "$p" ] && T+=("data/generated/targets/fusion360/$p"); done \
    < data/fusion360/ablation.txt
[ "${#T[@]}" -eq 36 ] || { echo "expected 36 ablation parts, got ${#T[@]}"; exit 1; }
if [ -n "${PARTS:-}" ]; then  # a subset of the 36, e.g. one batch
  ALL=" ${T[*]} "; T=()
  while IFS= read -r p; do [ -z "$p" ] && continue
    q="data/generated/targets/fusion360/$p"
    case "$ALL" in *" $q "*) T+=("$q") ;; *) echo "$p is not in ablation.txt"; exit 1 ;; esac
  done < "$PARTS"
fi
[ -n "${LIMIT:-}" ] && T=("${T[@]:0:$LIMIT}")
for p in "${T[@]}"; do [ -d "$p" ] || { echo "missing target $p (unpack A's inputs)"; exit 1; }; done
grep -q '^GOOGLE_CLOUD_PROJECT=..*' .env || { echo "set GOOGLE_CLOUD_PROJECT in .env"; exit 1; }

INIT=(--init data/generated/init/cadrille_rl)
case "${1:-required}" in
  required) CONFIGS=(
      "main_s1|${INIT[*]} --arm geo --seed 1"
      "gemini|--arm geo"
      "one_view|${INIT[*]} --arm geo --views worst"
      "no_gate|${INIT[*]} --arm geo --gate off"
      "patience1|${INIT[*]} --arm geo --patience 1"
      "patience2|${INIT[*]} --arm geo --patience 2") ;;
  secondary) CONFIGS=(
      "no_detail|${INIT[*]} --arm geo --no-detail"
      "no_kernel|${INIT[*]} --arm geo --no-kernel"
      "signed_resid|${INIT[*]} --arm geo --residual-view signed") ;;
  *) echo "usage: bash run_b.sh [required|secondary]"; exit 1 ;;
esac
LANES=${LANES:-3}
mkdir -p logs

for ((lane = 0; lane < LANES; lane++)); do
  cmds=""
  for ((i = lane; i < ${#CONFIGS[@]}; i += LANES)); do
    id=${CONFIGS[$i]%%|*}; flags=${CONFIGS[$i]#*|}
    name="${PREFIX:-}abl_$id${SUFFIX:-}"
    cmds+="echo \"=== $name start \$(date)\"; "
    cmds+="uv run python refine.py ${T[*]} $flags --rounds 6 ${EXTRA:-} --name $name; "
    cmds+="echo \"=== $name end \$(date)\"; "
  done
  [ -z "$cmds" ] && continue
  if [ -n "${DRY:-}" ]; then echo "lane $((lane + 1)): $cmds" | sed 's|data/generated/targets/fusion360/[^ ]* ||g'; continue; fi
  nohup caffeinate -i bash -c "$cmds" > "logs/run_b_lane$((lane + 1)).log" 2>&1 &
  echo "lane $((lane + 1)) (pid $!): $(for ((i = lane; i < ${#CONFIGS[@]}; i += LANES)); do
    printf '%s ' "${CONFIGS[$i]%%|*}"; done)"
done
echo "check progress with: uv run python check_runs.py"
