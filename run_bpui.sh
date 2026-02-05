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
    
    # Install from requirements.txt if it exists
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
    else
        # Fallback to manual installation
        pip install --quiet textual rich tomli-w httpx setuptools wheel
        # Add tomli for Python < 3.11
        python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" || pip install --quiet tomli
    fi
    
    echo "Installing bpui in editable mode..."
    pip install --quiet -e "$SCRIPT_DIR"
    
    echo "✓ Setup complete!"
fi

# Activate venv and run bpui
source "$VENV_DIR/bin/activate"

# Check for updates to dependencies
if [ "$1" = "--update-deps" ]; then
    echo "Updating dependencies..."
    pip install --quiet --upgrade pip
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install --quiet --upgrade -r "$SCRIPT_DIR/requirements.txt"
    fi
    pip install --quiet -e "$SCRIPT_DIR"
    echo "✓ Dependencies updated!"
    shift  # Remove --update-deps from args
fi

exec python -m bpui.cli "$@"
