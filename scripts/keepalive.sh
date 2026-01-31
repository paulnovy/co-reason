#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/marian/co-reason"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.keepalive"
mkdir -p "$LOG_DIR"

LOGFILE="$LOG_DIR/keepalive.log"

check_and_start_api() {
  if ! ss -tlnp | grep -q ':8000'; then
    echo "[$(date -Iseconds)] API down → starting" | tee -a "$LOGFILE"
    (cd "$BACKEND_DIR" && ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 & echo $! > /tmp/uvicorn.pid)
  fi
}

check_and_start_front() {
  if ! ss -tlnp | grep -q ':5173'; then
    echo "[$(date -Iseconds)] Front down → starting" | tee -a "$LOGFILE"
    (cd "$FRONTEND_DIR" && VITE_USE_GRAPH=false nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/frontend.log 2>&1 & echo $! > /tmp/frontend.pid)
  fi
}

check_and_start_api
check_and_start_front

# Health checks
curl -s --max-time 3 http://127.0.0.1:8000/ >/dev/null || echo "[$(date -Iseconds)] API health fail" | tee -a "$LOGFILE"
curl -s --max-time 3 http://127.0.0.1:5173/ >/dev/null || echo "[$(date -Iseconds)] Front health fail" | tee -a "$LOGFILE"

