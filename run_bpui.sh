#!/bin/bash
# Launcher script for Blueprint UI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
BPUI_CLI="$SCRIPT_DIR/bpui-cli"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found. Setting up..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    pip install --quiet textual rich tomli-w httpx setuptools wheel
fi

# Run bpui using direct CLI script (workaround for Python 3.13 editable install issues)
exec "$VENV_PYTHON" "$BPUI_CLI" "$@"
