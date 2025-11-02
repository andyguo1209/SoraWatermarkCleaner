#!/usr/bin/env bash

# Restart both backend (FastAPI) and frontend (Streamlit) services.
# Usage: ./restart_all.sh

set -euo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

kill_from_pid_file() {
  local pid_file=$1
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid=$(cat "${pid_file}" || true)
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      echo "🛑 Stopping process ${pid} recorded in ${pid_file}..."
      kill "${pid}" >/dev/null 2>&1 || true
      sleep 1
      if ps -p "${pid}" >/dev/null 2>&1; then
        kill -9 "${pid}" >/dev/null 2>&1 || true
      fi
    fi
    rm -f "${pid_file}"
  fi
}

echo "🛑 Stopping any existing backend/frontend processes..."
kill_from_pid_file "${LOG_DIR}/backend.pid"
kill_from_pid_file "${LOG_DIR}/frontend.pid"
pkill -f "python start_server.py" >/dev/null 2>&1 || true
pkill -f "streamlit run app.py" >/dev/null 2>&1 || true

sleep 1

echo "🚀 Starting backend (FastAPI) on port 5344..."
nohup uv run python start_server.py >"${LOG_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!
echo "${BACKEND_PID}" >"${LOG_DIR}/backend.pid"
echo "   Backend PID: ${BACKEND_PID} (logs: ${LOG_DIR}/backend.log)"

echo "🎬 Starting frontend (Streamlit) on default port..."
nohup uv run streamlit run app.py >"${LOG_DIR}/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "${FRONTEND_PID}" >"${LOG_DIR}/frontend.pid"
echo "   Frontend PID: ${FRONTEND_PID} (logs: ${LOG_DIR}/frontend.log)"

echo "✅ Restart complete. Use 'tail -f logs/backend.log' or 'tail -f logs/frontend.log' to watch logs."
