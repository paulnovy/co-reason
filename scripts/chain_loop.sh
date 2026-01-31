#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/marian/co-reason
LOG=$ROOT/.loop/loop.log
STATE=$ROOT/.loop/state.json
mkdir -p "$ROOT/.loop"

now=$(date +%s)
next_full=$(( (now/3600 + 1) * 3600 ))
secs_left=$(( next_full - now ))

echo "[$(date -Iseconds)] tick, secs_to_full_hour=$secs_left" | tee -a "$LOG"

# Stop within last 60s before full hour
if [ "$secs_left" -le 60 ]; then
  echo "[$(date -Iseconds)] STOP (full-hour review window)" | tee -a "$LOG"
  exit 0
fi

# One-iteration runner: pick next unchecked task and implement.
# For now this runner just records intent; actual work stays in the main agent turns.
# (We keep this script minimal and safe.)

echo "{\"lastTick\": $(date +%s), \"nextFullHour\": $next_full}" > "$STATE"

# Schedule next tick in 5 minutes
systemd-run --user --unit=po-loop-$(date +%s) --on-active=5min --no-block "$ROOT/scripts/chain_loop.sh" >/dev/null 2>&1 || true

echo "[$(date -Iseconds)] scheduled next tick via systemd-run --user" | tee -a "$LOG"
