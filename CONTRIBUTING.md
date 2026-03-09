# Contributing to Character Generator

This repository spans a Python backend, web app, Tauri desktop shell, shared TypeScript packages, and legacy Python-native interfaces. Keep changes small, verifiable, and aligned with the current architecture.

## Setup

```bash
pnpm install

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

Common launch commands:

```bash
# backend
python -m uvicorn bpui.api.main:app --reload

# web
pnpm dev:web

# desktop
./run_desktop.sh

# Textual TUI
./run_bpui.sh tui
```

## Testing

- Add tests for changed behavior when practical
- Normal pytest runs enforce the repo-wide coverage gate
- Use `--no-cov` for narrow local validation runs
- Rebuild `@char-gen/shared` before validating the web app if you changed shared types or the API client

Useful checks:

```bash
pytest -m "not slow"
pytest --no-cov tests/unit/test_cli.py
pnpm --filter @char-gen/shared build
pnpm --filter @char-gen/web exec tsc --noEmit
pnpm --filter @char-gen/web build
cd packages/desktop/src-tauri && cargo check
```

## Change Guidelines

### Python

- Follow the style of the touched module
- Use type hints for new or changed public interfaces
- Prefer focused fixes over broad refactors

### TypeScript / React

- Preserve package boundaries between `shared`, `web`, `desktop`, and `mobile`
- Keep API shapes centralized in `packages/shared` when possible

### Documentation

- Update docs when commands, defaults, workflows, or contracts change
- Treat `docs/archive/` as historical context, not current behavior

## Blueprint and Template Rules

- Do not break the generation contract
- Keep asset formats asset-specific
- Respect dependency order between assets
- Do not reintroduce retired official assets into the default template contract
- Keep placeholders and validator expectations explicit

Relevant locations:

- official shared blueprints: `blueprints/`
- project templates: `blueprints/templates/`
- user custom templates: `~/.config/bpui/templates/custom/`

## Pull Requests

Before opening a PR:

1. Run the smallest relevant validation set and record it.
2. Update docs for user-visible changes.
3. Call out migrations, breaking changes, or blueprint/template contract changes.
4. Keep the title and commits specific.

Preferred commit prefixes: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`.

## Good Contribution Targets

- stale docs and broken command references
- API/web/shared parity issues
- template/export regressions
- validator edge cases
- desktop launcher or Tauri integration bugs

## Questions

If a change may affect blueprint validity, export compatibility, or validator behavior, document the assumption in the PR instead of guessing.
