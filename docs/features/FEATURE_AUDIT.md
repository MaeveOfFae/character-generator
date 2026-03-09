# Feature Audit

Last updated: 2026-03-09

This file is a current-state snapshot of the project. It is intentionally concise and only describes features that are relevant to the codebase as it exists now.

## Product Surfaces

### Web App

Status: active

- React + Vite frontend in `packages/web`
- uses the shared TypeScript API client from `packages/shared`
- talks to the FastAPI backend for drafts, generation, export, lineage, similarity, and validation

### Desktop App

Status: active

- Tauri wrapper in `packages/desktop`
- launched through `run_desktop.sh` / `run_desktop.bat`
- export uses a native save dialog path in the desktop shell

### Python CLI and TUI

Status: active

- CLI entrypoint in `bpui.core.cli`
- Textual TUI under `bpui.tui`
- useful for local workflows, scripting, validation, and review

### Mobile Workspace

Status: present

- Expo workspace under `packages/mobile`
- shares the same backend/API model

### Legacy Qt GUI

Status: maintained but not primary

- code lives under `bpui.gui`
- still available when PySide6 is installed
- should be documented as legacy rather than the recommended surface

## Generation and Templates

Status: active

- generation is template-aware, not hard-coded to a single asset count
- the official built-in template is `V2/V3 Card`
- the current official shared asset chain is:
  - `system_prompt`
  - `post_history`
  - `character_sheet`
  - `intro_scene`
  - `intro_page`
  - `a1111`
- template manifests declare assets, dependencies, and optional blueprint overrides
- custom templates are loaded from `~/.config/bpui/templates/custom/`

## Drafts and Metadata

Status: active

- drafts are stored under `drafts/`
- each draft includes `.metadata.json`
- draft indexing uses SQLite at `drafts/.index.db`
- review and validation flows are template-aware and should not assume a single official filename set

## Export

Status: active

- preset definitions live under `presets/`
- raw export zips the real top-level `.txt` and `.md` files present in a draft
- preset export maps only assets that exist for the selected draft/template
- API export responses preserve filenames via `Content-Disposition`
- desktop export now writes through a native Tauri command path

## Analysis and Workflow Features

Status: active

- similarity analysis
- lineage views
- offspring generation
- validation endpoints and CLI/TUI flows
- chat refinement
- batch workflows and seed generation

## Backend API

Status: active

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

## Quality Gates

Status: active

- repo-wide pytest coverage gate remains enabled
- focused local runs should use `--no-cov`
- web changes should be validated with TypeScript build checks
- desktop changes should be validated with `cargo check`

## Documentation Constraints

- `docs/archive/` contains historical material and may mention retired blueprint contracts or older UI assumptions
- current docs should describe the web/desktop/API-centered architecture first
