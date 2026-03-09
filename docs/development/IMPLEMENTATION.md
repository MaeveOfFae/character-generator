# Implementation Overview

This document describes the current high-level architecture of the project rather than the historical rollout sequence.

## System Shape

Character Generator is split into five main layers:

1. `blueprints/`: official orchestrator, shared asset blueprints, and template manifests
2. `bpui/`: Python backend and core generation logic
3. `packages/shared/`: shared TypeScript types and API client
4. `packages/web` and `packages/mobile`: frontend clients
5. `packages/desktop`: Tauri desktop shell around the web client

## Runtime Model

### Backend

`bpui.api.main:app` is the FastAPI application used by the web app, desktop shell, and mobile workspace.

Key responsibilities:

- configuration and model access
- draft CRUD
- generation and batch generation
- export presets and download responses
- similarity, offspring, lineage, and validation endpoints

### Python-Native Interfaces

The Python layer also exposes:

- `bpui` CLI commands through `bpui.core.cli`
- Textual TUI screens under `bpui.tui`
- a legacy PySide6 GUI under `bpui.gui`

These still matter for local workflows, but the modern product-facing UI is the web app plus the Tauri desktop wrapper.

## Generation Flow

At a high level:

1. A user selects a template and provides a seed.
2. The backend resolves the template's assets and dependency graph.
3. Prompts are built from the shared orchestrator or asset-specific blueprint text.
4. The configured LLM adapter generates content.
5. Output is parsed into template-defined assets.
6. The resulting draft is written to `drafts/<timestamp>_<name>/` with `.metadata.json`.
7. Review, validation, export, lineage, and similarity features operate on that saved draft.

## Template System

The template system is no longer a fixed seven-asset contract.

Current behavior:

- the official built-in template is `V2/V3 Card`
- the official shared asset chain is `system_prompt`, `post_history`, `character_sheet`, `intro_scene`, `intro_page`, `a1111`
- template manifests define assets, dependencies, and optional template-local blueprint files
- custom templates are discovered from `~/.config/bpui/templates/custom/`

This means parsing, validation, and export all need to remain template-aware.

## Drafts and Export

Drafts are directories containing top-level `.txt` and `.md` assets plus metadata.

Important implementation details:

- draft identification should use the review/draft directory ID, not the seed string
- raw export zips the actual top-level asset files present in the draft
- preset export maps only assets that exist for that draft's template
- desktop export uses a native Tauri save dialog rather than browser-only download behavior

## Search and Metadata

Draft indexing lives in `bpui.utils.metadata.draft_index` and stores data in `drafts/.index.db`.

The index supports:

- search across names, seeds, tags, and notes
- filtering by mode and favorite status
- rebuilds from disk using `bpui rebuild-index`

## Shared Frontend Contract

Frontend API shapes belong in `packages/shared`.

When backend contracts change:

1. update the backend response/request model
2. update the shared TypeScript client and types
3. rebuild `@char-gen/shared`
4. validate web and desktop clients against the new contract

## Validation Targets

Useful checks during development:

```bash
pytest -m "not slow"
pytest --no-cov tests/unit/test_cli.py
pnpm --filter @char-gen/shared build
pnpm --filter @char-gen/web exec tsc --noEmit
pnpm --filter @char-gen/web build
cd packages/desktop/src-tauri && cargo check
```

## Documentation Scope

This file is intentionally high level. For current usage and commands, prefer:

- `README.md`
- `docs/guides/QUICKSTART.md`
- `docs/installation/INSTALL.md`
- `bpui/README.md`

## Running the TUI

```bash
# With venv launcher (auto-setup)
./run_bpui.sh

# Or directly if installed
bpui

# Or with python module
python -m bpui.cli

# CLI mode
bpui compile --seed "..." --mode NSFW
bpui seed-gen --input genres.txt
bpui validate drafts/...
bpui export "Character Name" drafts/...
```

## Conclusion

The Blueprint UI implementation provides a complete, production-ready terminal interface for RPBotGenerator character compilation. It preserves the strict blueprint contract while adding convenient workflows for generation, validation, and export. The dual LLM adapter system ensures compatibility with both hosted providers and local models, meeting the "any LLM" requirement.
