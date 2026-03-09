# Character Generator

Character Generator is a template-aware character asset pipeline built around a Python/FastAPI backend, shared blueprint system, and multiple client surfaces. The current project center of gravity is the web app and Tauri desktop shell, with the Python CLI, TUI, and legacy Qt GUI still available for local workflows.

## Current State

- Official default template: `V2/V3 Card`
- Official shared asset set: `system_prompt`, `post_history`, `character_sheet`, `intro_scene`, `intro_page`, `a1111`
- Export is template-aware and asset-driven: presets only map assets that actually exist in the selected draft
- Desktop export uses a native Tauri save dialog
- Backend API powers web, desktop, mobile, and Python-side tools from the same draft/template store

## Quick Start

### Web App

```bash
pnpm install

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# terminal 1
python -m uvicorn bpui.api.main:app --reload

# terminal 2
pnpm dev:web
```

Open `http://localhost:3000`. Live API docs are available at `http://localhost:8000/docs`.

### Desktop App

The desktop launcher starts the API and Tauri shell together.

```bash
# Linux / macOS
./run_desktop.sh

# Windows
run_desktop.bat

# Optional dependency refresh first
./run_desktop.sh --update-deps
```

Desktop prerequisites:

- Python 3.10+
- `pnpm`
- Rust/Cargo
- On Linux, GTK/WebKitGTK development libraries

Ubuntu/Debian packages:

```bash
sudo apt install -y libgtk-3-dev libwebkit2gtk-4.1-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev librsvg2-dev pkg-config
```

### Python Interfaces

```bash
# Legacy Qt GUI launcher
./run_bpui.sh

# Textual TUI
./run_bpui.sh tui

# CLI help
bpui --help
```

### Mobile Workspace

An Expo workspace lives in `packages/mobile`.

```bash
pnpm dev:mobile
```

## Core Capabilities

- Template-aware generation from a single seed
- Draft review, editing, validation, export, and lineage tracking
- SSE-backed generation, offspring, chat refinement, and batch workflows
- Preset-based export for raw, combined, and platform-specific outputs
- Similarity analysis and redundancy detection
- Draft indexing for fast local search

## Architecture

```text
character-generator/
├── packages/
│   ├── shared/          # Shared TypeScript types and API client
│   ├── web/             # React + Vite app
│   ├── mobile/          # Expo / React Native app
│   └── desktop/         # Tauri wrapper around the web app
├── bpui/
│   ├── api/             # FastAPI app and routers
│   ├── core/            # CLI, config, theme, parser, orchestration helpers
│   ├── features/        # Templates, export, lineage, similarity, offspring
│   ├── gui/             # Legacy Qt GUI
│   ├── tui/             # Textual terminal UI
│   └── utils/           # Draft IO, indexing, logging, metadata utilities
├── blueprints/          # Official orchestrator and shared blueprints
├── presets/             # Export preset definitions
├── drafts/              # Saved draft directories
└── docs/                # Project documentation
```

## API Surface

The FastAPI app lives at `bpui.api.main:app`. Major route groups:

- `/api/config`
- `/api/models`
- `/api/templates`
- `/api/blueprints`
- `/api/drafts`
- `/api/generate`
- `/api/seedgen`
- `/api/similarity`
- `/api/offspring`
- `/api/lineage`
- `/api/export`
- `/api/chat`
- `/api/validate`

## Common Commands

```bash
# compile a draft
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW

# batch compile
bpui batch --input seeds.txt --mode SFW --continue-on-error

# seed generation
bpui seed-gen --input genres.txt --out seed-output/noir.txt

# validate a draft or export
bpui validate drafts/20260307_203638_unnamed_character

# export with a preset
bpui export "Character Name" drafts/20260307_203638_unnamed_character --preset raw

# compare drafts
bpui similarity draft_a draft_b --use-llm

# lineage
bpui lineage
```

## Drafts, Templates, and Export

- Drafts are saved under `drafts/` with metadata in `.metadata.json`
- Template definitions are loaded from `blueprints/templates/` and `~/.config/bpui/templates/custom/`
- The official template manager also exposes the built-in `V2/V3 Card` template
- Raw export zips the actual top-level `.txt` and `.md` files present in a draft
- Preset exports only emit mapped assets that exist for that draft's template

## Testing

```bash
# full suite
pytest

# faster local loop
pytest -m "not slow"

# narrow runs without failing coverage gate
pytest --no-cov tests/unit/test_cli.py

# web typecheck/build
pnpm --filter @char-gen/web exec tsc --noEmit
pnpm --filter @char-gen/web build

# desktop validation
cd packages/desktop/src-tauri && cargo check
```

## Documentation

- [docs/README.md](docs/README.md): documentation index
- [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md): fast setup and first workflows
- [docs/installation/INSTALL.md](docs/installation/INSTALL.md): installation details
- [bpui/README.md](bpui/README.md): Python CLI, TUI, GUI, and backend notes
- [blueprints/README.md](blueprints/README.md): blueprint and template layout
- [docs/development/IMPLEMENTATION.md](docs/development/IMPLEMENTATION.md): current architecture summary

Historical notes and superseded implementation documents remain under `docs/archive/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## License

[BSD 3-Clause License](LICENSE)
