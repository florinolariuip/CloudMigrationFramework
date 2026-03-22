#!/usr/bin/env bash
set -euo pipefail

# Simple runner to start both backend (Flask) and frontend (static server)
# - Activates/creates local venv
# - Installs backend deps
# - Starts backend on port 5055 (reuses if already running)
# - Serves frontend on configurable port (default 8080)
# - Opens browser

# --- Config ---
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-5055}"
OPEN_BROWSER="${OPEN_BROWSER:-1}"
FLASK_DEBUG_ENV="${FLASK_DEBUG:-False}"

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
VENV_DIR="${ROOT_DIR}/.venv"
PY_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

# --- Helpers ---
log() { printf "\033[1;34m[run]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[err]\033[0m %s\n" "$*"; }

# Kill processes using specified ports if needed
kill_port() {
  local port="$1"
  local pids
  pids=$(lsof -ti:"$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    log "Killing processes using port ${port}: ${pids}"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

wait_for_health() {
  local url="$1"; local tries=${2:-30}; local delay=${3:-0.5}
  for ((i=1; i<=tries; i++)); do
    if curl -fsS -m 1 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

kill_if_running() {
  local pid="$1"
  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" || true
    wait "$pid" 2>/dev/null || true
  fi
}

# --- Python env ---
if [[ ! -x "$PY_BIN" ]]; then
  log "Creating virtual environment at ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

log "Python: $("$PY_BIN" -V)"

# --- Dependencies ---
log "Installing backend dependencies..."
"$PIP_BIN" install -q -r "${BACKEND_DIR}/requirements.txt"

# --- Kill any processes using our ports ---
kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

# --- Backend ---
HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/health"
BE_PID=""
FE_PID=""

if curl -fsS -m 1 "$HEALTH_URL" >/dev/null 2>&1; then
  log "Backend already running on ${BACKEND_PORT} (health OK)"
else
  log "Starting backend (Flask) on port ${BACKEND_PORT}..."
  export FLASK_DEBUG="${FLASK_DEBUG_ENV}"
  export SKIP_EXPERIMENTS=1
  
  # Create the start_be.command file first
  cat > "${ROOT_DIR}/start_be.command" <<EOF
#!/bin/bash
cd "${ROOT_DIR}"
"${PY_BIN}" -m flask --app backend.app:app run --host 127.0.0.1 --port "${BACKEND_PORT}" --no-reload
EOF
  chmod +x "${ROOT_DIR}/start_be.command"
  
  # Start backend in a new Terminal window (console only, no log file)
  open -a Terminal "${ROOT_DIR}/start_be.command"

  log "Waiting for backend health at ${HEALTH_URL}..."
  if ! wait_for_health "$HEALTH_URL" 60 0.5; then
    err "Backend failed to become healthy. See ${BACKEND_DIR}/.backend.log"
    exit 1
  fi
  log "Backend is healthy."
fi

# --- Frontend ---
log "Serving frontend from ${FRONTEND_DIR} on http://localhost:${FRONTEND_PORT}"

# Create the start_fe.command file first
cat > "$FRONTEND_DIR/start_fe.command" <<EOF
#!/bin/bash
cd "${FRONTEND_DIR}"
"${PY_BIN}" -m http.server "$FRONTEND_PORT" --bind 127.0.0.1
EOF
chmod +x "$FRONTEND_DIR/start_fe.command"

# Start frontend in a new Terminal window, ensuring correct working directory
open -a Terminal "$FRONTEND_DIR/start_fe.command"

# Give the server a moment, then open the browser
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
sleep 0.5 || true
if [[ "$OPEN_BROWSER" == "1" ]]; then
  log "Opening ${FRONTEND_URL}"
  command -v open >/dev/null 2>&1 && open "$FRONTEND_URL" || true
fi

log "Both servers started in separate Terminal windows."
