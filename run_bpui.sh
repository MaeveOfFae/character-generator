#!/bin/bash
# Launcher script for Blueprint UI

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found. Setting up..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    echo "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet textual rich tomli-w httpx setuptools wheel
    
    echo "Installing bpui in editable mode..."
    pip install --quiet -e "$SCRIPT_DIR"
fi

# Activate venv and run bpui
source "$VENV_DIR/bin/activate"
exec python -m bpui.cli "$@"
