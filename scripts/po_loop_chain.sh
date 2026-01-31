#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/marian/co-reason"
TICK_MINUTES=5
STOP_SECONDS=60

now=$(date +%s)
next_full=$(( (now/3600 + 1) * 3600 ))
secs_left=$(( next_full - now ))

# Stop close to top of hour
if [ "$secs_left" -le "$STOP_SECONDS" ]; then
  echo "STOP: within ${STOP_SECONDS}s of full hour (secs_left=$secs_left)."
  exit 0
fi

# Determine next run
# If next tick would land inside stop window, do not schedule.
next_tick=$(( now + TICK_MINUTES*60 ))
secs_left_next=$(( next_full - next_tick ))
if [ "$secs_left_next" -le "$STOP_SECONDS" ]; then
  echo "STOP: next tick would cross into review window."
  exit 0
fi

# Build next payload. Keep it short; real source of truth is spec/plan.
PAYLOAD=$'PO LOOP ITERATION (chained):\n- Read spec.md + implementation_plan.md in /home/marian/co-reason.\n- Do ONE highest-leverage unchecked task.\n- Verify (pytest/curl).\n- Check it off.\n- Then run scripts/po_loop_chain.sh again to schedule next tick (unless within 60s of full hour).'

# Schedule next tick via OpenClaw cron CLI (main session systemEvent)
openclaw cron add \
  --name "po-loop-tick" \
  --session main \
  --wake now \
  --at "+${TICK_MINUTES}m" \
  --system-event "$PAYLOAD" \
  --timeout 60000 \
  >/dev/null

echo "Scheduled next tick in ${TICK_MINUTES}m (secs_left=$secs_left)."
