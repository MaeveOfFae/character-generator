# bpui

`bpui` is the Python layer of Character Generator. It provides the FastAPI backend, CLI, Textual TUI, legacy Qt GUI, and the core template, draft, validation, and export logic used by the other app surfaces.

## Modules

- `bpui.api`: FastAPI application and routers
- `bpui.core`: CLI, config, parsing, orchestration, and theme helpers
- `bpui.features`: templates, export, lineage, similarity, offspring, and related feature modules
- `bpui.tui`: Textual terminal UI
- `bpui.gui`: legacy PySide6 GUI
- `bpui.utils`: draft IO, metadata, indexing, logging, and utility helpers

## Launching

### Recommended surfaces

```bash
# web + backend
python -m uvicorn bpui.api.main:app --reload
pnpm dev:web

# desktop shell + backend
./run_desktop.sh
```

### Python-native surfaces

```bash
# legacy Qt GUI
./run_bpui.sh

# Textual TUI
./run_bpui.sh tui

# CLI
bpui --help
```

`run_bpui.sh` creates `.venv` if needed, installs Python dependencies, and runs `python -m bpui.core.cli`.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Optional dependency for the legacy GUI:

```bash
pip install PySide6
```

## Current Defaults

- Official template: `V2/V3 Card`
- Official asset chain: `system_prompt -> post_history -> character_sheet -> intro_scene -> intro_page -> a1111`
- Draft root: `drafts/`
- Custom templates: `~/.config/bpui/templates/custom/`
- Draft index database: `drafts/.index.db`

## CLI Examples

```bash
bpui compile --seed "Noir detective with psychic abilities" --mode SFW
bpui batch --input seeds.txt --continue-on-error
bpui seed-gen --input genres.txt --out seed-output/noir.txt
bpui validate drafts/20260307_203638_unnamed_character
bpui export "Character Name" drafts/20260307_203638_unnamed_character --preset raw
bpui rebuild-index
bpui similarity draft_a draft_b --use-llm
bpui lineage
bpui versions draft_name character_sheet --list
bpui rehash draft_name --variation twist
```

Use `bpui --help` for the full command set.

## Backend Routes

The backend entrypoint is `bpui.api.main:app`.

Primary route groups:

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

## Parser and Template Notes

- Parsing is template-aware rather than hard-wired to a single legacy asset count
- The built-in official template still resolves to the `V2/V3 Card` asset chain
- Template-backed drafts can use different filenames from the official shared template
- Raw export preserves the draft's actual top-level `.txt` and `.md` files

## Development Checks

```bash
pytest -m "not slow"
pytest --no-cov tests/unit/test_cli.py
pnpm --filter @char-gen/web exec tsc --noEmit
cd packages/desktop/src-tauri && cargo check
```

For a broader project overview, see [../README.md](../README.md).

Same as parent repository.
