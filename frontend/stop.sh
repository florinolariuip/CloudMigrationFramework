#!/usr/bin/env bash
set -euo pipefail

# Stop local dev servers started by frontend/start.sh
# - Kills backend Flask (uses backend/.backend.pid if present; else kills by port)
# - Kills frontend http.server on FRONTEND_PORT (default 8080)

FRONTEND_PORT="${FRONTEND_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-5055}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

log() { printf "\033[1;34m[stop]\033[0m %s\n" "$*"; }

# Stop backend by PID file if present
if [[ -f "${BACKEND_DIR}/.backend.pid" ]]; then
  BE_PID="$(cat "${BACKEND_DIR}/.backend.pid" || true)"
  if [[ -n "${BE_PID}" ]] && kill -0 "${BE_PID}" 2>/dev/null; then
    log "Stopping backend (pid ${BE_PID})"
    kill "${BE_PID}" 2>/dev/null || true
    sleep 0.5
    rm -f "${BACKEND_DIR}/.backend.pid"
  fi
fi

# Fallback: kill any process listening on BACKEND_PORT
BE_PIDS=$(lsof -ti:"${BACKEND_PORT}" 2>/dev/null || true)
if [[ -n "${BE_PIDS}" ]]; then
  log "Killing backend processes on port ${BACKEND_PORT}: ${BE_PIDS}"
  echo "${BE_PIDS}" | xargs kill -9 2>/dev/null || true
fi

# Kill frontend http.server
FE_PIDS=$(lsof -ti:"${FRONTEND_PORT}" 2>/dev/null || true)
if [[ -n "${FE_PIDS}" ]]; then
  log "Killing frontend http.server on port ${FRONTEND_PORT}: ${FE_PIDS}"
  echo "${FE_PIDS}" | xargs kill -9 2>/dev/null || true
fi

log "Done."
