#!/bin/bash
# Launcher script for Character Generator Desktop (Tauri)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
API_HOST="127.0.0.1"
API_PORT="8000"
API_URL="http://${API_HOST}:${API_PORT}/api/health"
API_PID=""
SANITIZED_DESKTOP_ENV=(
    env
    -u GTK_PATH
    -u GIO_MODULE_DIR
    -u LD_LIBRARY_PATH
    -u SNAP
    -u SNAP_ARCH
    -u SNAP_COMMON
    -u SNAP_CONTEXT
    -u SNAP_COOKIE
    -u SNAP_DATA
    -u SNAP_INSTANCE_KEY
    -u SNAP_INSTANCE_NAME
    -u SNAP_LIBRARY_PATH
    -u SNAP_NAME
    -u SNAP_REAL_HOME
    -u SNAP_REVISION
    -u SNAP_USER_COMMON
    -u SNAP_USER_DATA
    -u SNAP_VERSION
)

api_listener_pids() {
    lsof -tiTCP:"$API_PORT" -sTCP:LISTEN 2>/dev/null || true
}

is_repo_api_process() {
    local pid="$1"
    local command_line

    command_line="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    [[ "$command_line" == *"uvicorn bpui.api.main:app"* ]] || [[ "$command_line" == *"-m uvicorn bpui.api.main:app"* ]]
}

stop_existing_api() {
    local existing_pids=()
    local pid
    local command_line
    local attempt

    while IFS= read -r pid; do
        [ -n "$pid" ] && existing_pids+=("$pid")
    done < <(api_listener_pids)

    if [ ${#existing_pids[@]} -eq 0 ]; then
        return 0
    fi

    for pid in "${existing_pids[@]}"; do
        command_line="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        if ! is_repo_api_process "$pid"; then
            echo "Error: Port ${API_PORT} is already in use by a non-bpui process:"
            echo "  PID ${pid}: ${command_line:-<unknown>}"
            echo "Refusing to kill it automatically. Stop that process or change the API port in the launcher."
            exit 1
        fi
    done

    echo "Restarting existing local API process on port ${API_PORT}..."
    for pid in "${existing_pids[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    for pid in "${existing_pids[@]}"; do
        for attempt in $(seq 1 20); do
            if ! kill -0 "$pid" 2>/dev/null; then
                break
            fi
            sleep 0.25
        done

        if kill -0 "$pid" 2>/dev/null; then
            echo "Process ${pid} did not stop after SIGTERM; forcing shutdown..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
}

cleanup() {
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

require_command() {
    local command_name="$1"
    local install_hint="$2"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Error: '$command_name' is required. $install_hint"
        exit 1
    fi
}

check_linux_tauri_deps() {
    if [ "$(uname -s)" != "Linux" ]; then
        return 0
    fi

    require_command pkg-config "Install pkg-config so native desktop dependencies can be detected."

    local missing=()

    pkg-config --exists gtk+-3.0 || missing+=("gtk+-3.0")
    pkg-config --exists webkit2gtk-4.1 || pkg-config --exists webkit2gtk-4.0 || missing+=("webkit2gtk")
    pkg-config --exists libsoup-3.0 || missing+=("libsoup-3.0")
    pkg-config --exists javascriptcoregtk-4.1 || pkg-config --exists javascriptcoregtk-4.0 || missing+=("javascriptcoregtk")

    if [ ${#missing[@]} -eq 0 ]; then
        return 0
    fi

    echo "Error: Missing native Linux libraries required for the Tauri desktop build: ${missing[*]}"
    echo
    echo "Install the usual Ubuntu/Debian packages:"
    echo "  sudo apt install -y libgtk-3-dev libwebkit2gtk-4.1-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev librsvg2-dev"
    echo
    echo "If your distro only ships the 4.0 WebKitGTK line, install the equivalent 4.0 dev packages instead."
    exit 1
}

ensure_python_env() {
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "Virtual environment not found. Setting up..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"

        echo "Installing Python dependencies..."
        pip install --quiet --upgrade pip
        pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
        pip install --quiet -e "$SCRIPT_DIR"
        echo "✓ Python environment ready"
        return
    fi

    source "$VENV_DIR/bin/activate"
}

ensure_node_deps() {
    if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
        echo "Node dependencies not found. Installing with pnpm..."
        (cd "$SCRIPT_DIR" && pnpm install)
        echo "✓ Node dependencies installed"
    fi
}

wait_for_api() {
    local attempt
    for attempt in $(seq 1 30); do
        if curl -fsS "$API_URL" >/dev/null 2>&1; then
            return 0
        fi

        if ! kill -0 "$API_PID" 2>/dev/null; then
            echo "Error: API server exited before becoming ready"
            return 1
        fi

        sleep 1
    done

    echo "Error: API server did not become ready at $API_URL"
    return 1
}

require_command python3 "Install Python 3.10+ and make sure it is on your PATH."
require_command pnpm "Install pnpm 9+ and make sure it is on your PATH."
require_command cargo "Install Rust/Cargo; Tauri needs a Rust toolchain."
require_command curl "Install curl so the launcher can detect when the API is ready."
check_linux_tauri_deps

ensure_python_env

if [ "${1:-}" = "--update-deps" ]; then
    echo "Updating Python and Node dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet --upgrade -r "$SCRIPT_DIR/requirements.txt"
    pip install --quiet -e "$SCRIPT_DIR"
    (cd "$SCRIPT_DIR" && pnpm install)
    echo "✓ Dependencies updated"
    shift
fi

ensure_node_deps
stop_existing_api

echo "Starting API server on ${API_HOST}:${API_PORT}..."
(
    cd "$SCRIPT_DIR"
    exec "$VENV_PYTHON" -m uvicorn bpui.api.main:app --host "$API_HOST" --port "$API_PORT"
) &
API_PID=$!

wait_for_api

echo "Launching desktop app..."
cd "$SCRIPT_DIR"
"${SANITIZED_DESKTOP_ENV[@]}" pnpm tauri:dev "$@"