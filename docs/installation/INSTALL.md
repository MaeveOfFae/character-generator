# Installation

This guide covers the current setup paths for the project.

## Requirements

- Python 3.10+
- Node.js 20+
- `pnpm` 9+
- Rust/Cargo for the Tauri desktop shell
- On Linux desktop builds, GTK/WebKitGTK development libraries

Ubuntu/Debian packages for Linux desktop builds:

```bash
sudo apt install -y libgtk-3-dev libwebkit2gtk-4.1-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev librsvg2-dev pkg-config
```

## Base Setup

```bash
pnpm install

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Launch Options

### Web App

```bash
# terminal 1
python -m uvicorn bpui.api.main:app --reload

# terminal 2
pnpm dev:web
```

### Desktop App

```bash
./run_desktop.sh
```

The desktop launcher ensures the Python environment exists, installs Node dependencies if needed, starts `bpui.api.main:app`, and launches the Tauri shell.

### Python Interfaces

```bash
# legacy Qt GUI
./run_bpui.sh

# Textual TUI
./run_bpui.sh tui

# CLI
bpui --help
```

If you want the legacy GUI outside the launcher, install PySide6:

```bash
pip install PySide6
```

## Configuration

Settings are stored in `.bpui.toml`.

OpenRouter via the OpenAI-compatible engine:

```toml
engine = "openai_compatible"
model = "openrouter/openai/gpt-4o-mini"
base_url = "https://openrouter.ai/api/v1"
temperature = 0.7
max_tokens = 4096

[api_keys]
openrouter = "sk-or-v1-..."
```

Local OpenAI-compatible server example:

```toml
engine = "openai_compatible"
model = "llama3.1"
base_url = "http://localhost:11434/v1"
```

## Validation Checks

```bash
pytest -m "not slow"
pnpm --filter @char-gen/web exec tsc --noEmit
cd packages/desktop/src-tauri && cargo check
```

## Common Commands

```bash
bpui compile --seed "Noir detective with psychic abilities" --mode SFW
bpui seed-gen --input genres.txt --out seed-output/noir.txt
bpui validate drafts/20260307_203638_unnamed_character
bpui export "Character Name" drafts/20260307_203638_unnamed_character --preset raw
```

## Troubleshooting

### Desktop build fails on Linux

Install the GTK/WebKitGTK development packages listed above. `run_desktop.sh` checks for them before launch.

### `bpui` launches the legacy GUI but you want the TUI

Use `bpui tui` or `./run_bpui.sh tui`.

### API connection issues

Check that:

- the model name matches the provider you configured
- the relevant key exists in `[api_keys]`
- `base_url` is correct for local OpenAI-compatible servers
- the backend responds at `http://localhost:8000/api/health`

### Narrow pytest runs fail on coverage

The repo-wide coverage gate still applies. Use `--no-cov` when validating a narrow slice.

## Next Steps

- [../guides/QUICKSTART.md](../guides/QUICKSTART.md)
- [../../bpui/README.md](../../bpui/README.md)
- [../../blueprints/README.md](../../blueprints/README.md)
