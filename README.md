# Eidolon Simulacra

Eidolon Simulacra is a pnpm monorepo for template-aware character generation. The current product surface is a browser-first React app backed by shared TypeScript generation, parsing, export, and template utilities.

The repo is centered on a strict blueprint contract: start from one seed, generate assets in dependency order, keep asset formats module-specific, and do not leak downstream facts upstream.

## Current State

- Browser-only workflow for day-to-day use. Drafts, templates, blueprint edits, and theme choices stay in browser storage.
- Direct LLM provider integration from the client via the shared engine layer.
- Two official template families in the repo:
  - `V2/V3 Card` with `system_prompt`, `post_history`, `character_sheet`, `intro_scene`, `intro_page`, and `a1111`
  - `Official Aksho` with the split eight-asset flow from `system_prompt` through `initial_message`
- Shared parser and validator utilities for fenced-codeblock generation output.
- Export helpers and preset definitions for raw asset packs and platform-specific formats.
- Rule and workflow documentation under `rules/` for generation constraints, content modes, and blueprint hygiene.

## Workspace Layout

```text
character-generator/
├── blueprints/          # Orchestrators, template manifests, template-local asset blueprints
├── packages/
│   ├── shared/          # Shared TS types, generation, parsing, export, template utilities
│   ├── web/             # React 19 + Vite browser app
│   └── mobile/          # Early mobile scaffold, not part of the current build/lint flow
├── presets/             # Export preset definitions
├── resources/           # Theme/resource files tracked in the repo
├── rules/               # Generation contract, content rules, and workflow docs
└── tools/               # Supporting docs and generation notes
```

## Web App

The web app currently exposes the main workflows directly in the browser:

- Generate from a seed with template selection and content mode controls
- Generate seed ideas and carry them into the main generation flow
- Review, edit, validate, compare, and export drafts
- Browse and edit templates and blueprint source
- Run offspring and similarity workflows
- Manage themes, browser-stored data, and app settings

The home screen also calls out the current operating mode explicitly: browser-only, no local API server required for normal usage.

## Quick Start

Requirements:

- Node.js 20+
- pnpm 9+

Install and run the web app:

```bash
pnpm install
pnpm dev:web
```

Vite will print the local URL in the terminal. By default that is usually `http://localhost:5173`.

To expose the app on your local network:

```bash
pnpm dev:web:lan
```

That launches Vite on port `3000` with host `0.0.0.0`.

## Common Commands

```bash
# Start all configured dev tasks through Turbo
pnpm dev

# Build shared package only
pnpm build:shared

# Build the web app and its shared dependency
pnpm build:web

# Build the current workspace graph
pnpm build

# Lint packages that participate in CI
pnpm lint

# Format tracked source/docs globs
pnpm format
```

Notes:

- The current CI path builds and lints `@char-gen/shared` and `@char-gen/web`.
- `packages/mobile` exists in the workspace, but it is not wired into the root build or lint tasks yet.
- The root `test` pipeline exists in Turbo, but there are no package-level automated test tasks checked in right now.

## Generation Model

The generation system is template-driven.

- System orchestrators live in `blueprints/system/`.
- Official templates live in `blueprints/templates/` and declare asset order with `depends_on` in `template.toml`.
- Shared parsing utilities map fenced codeblocks back into asset files and run fatal contract checks for placeholders and format violations.
- The default official template is still the six-asset V2/V3 flow, but the repo also supports template-specific asset graphs such as Aksho.

If you are editing blueprints, start with `rules/60_blueprint_hard_rules.md` and `blueprints/README.md`.

## Exports, Presets, and Themes

- The browser app currently exposes built-in export modes for JSON, plain text, and combined markdown bundles.
- The `presets/` directory stores TOML preset definitions for raw packs and platform-oriented exports such as Chub AI, RisuAI, and TavernAI.
- Theme and resource files tracked in `resources/` are repository assets; the current browser runtime uses built-in theme presets defined in code plus browser-stored customizations.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## License

[BSD 3-Clause License](LICENSE)
