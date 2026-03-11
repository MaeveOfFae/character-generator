# Contributing to Character Generator

Character Generator currently ships as a TypeScript monorepo with a browser-first web app and shared generation utilities. Keep changes narrow, verifiable, and aligned with the current repo shape rather than older Python or desktop workflows.

## Setup

Requirements:

- Node.js 20+
- pnpm 9+

Install dependencies:

```bash
pnpm install
```

Common local commands:

```bash
# web app
pnpm dev:web

# shared package build
pnpm build:shared

# web production build
pnpm build:web

# repo lint
pnpm lint

# formatting
pnpm format
```

There is no checked-in Python backend, Tauri desktop shell, or Textual launcher in the current workspace. Do not add doc references to those paths unless they actually land in the repo.

## Validation

Run the smallest relevant checks for the area you changed.

Useful commands:

```bash
pnpm --filter @char-gen/shared build
pnpm --filter @char-gen/web build
pnpm --filter @char-gen/web exec tsc --noEmit
pnpm lint
```

Notes:

- CI currently covers lint plus the shared and web builds.
- `@char-gen/shared` publishes from `dist/`, so rebuild it before validating web changes that depend on updated shared exports.
- The root Turbo pipeline includes a `test` task, but package-level automated test tasks are not currently checked in.
- `packages/mobile` is present as a scaffold and should not be assumed to participate in CI unless you wire it up explicitly.

## Change Guidelines

### TypeScript and React

- Preserve package boundaries between `packages/shared`, `packages/web`, and `packages/mobile`.
- Keep shared types, parsing helpers, export logic, and cross-surface contracts in `packages/shared` when possible.
- Avoid documenting API-server behavior as current product behavior unless the implementation exists in this repo.

### Documentation

- Update docs whenever commands, defaults, workflows, storage behavior, or blueprint contracts change.
- Prefer describing the current shipping path over historical or aspirational architecture.
- If a feature is scaffolded but not wired into the build, say that directly.

### Blueprints and Templates

- Do not break the generation contract.
- Keep asset formats asset-specific.
- Respect dependency order between assets.
- Do not move downstream facts into upstream assets.
- Keep placeholder and control-block requirements explicit.

Relevant locations:

- `blueprints/system/` for orchestrators
- `blueprints/templates/` for template manifests and template-local asset blueprints
- `rules/` for repo constraints and workflow guidance
- `presets/` for export preset definitions

## Pull Requests

Before opening a PR:

1. Run the smallest relevant validation set and note what you ran.
2. Update docs for user-visible behavior, commands, or workflow changes.
3. Call out blueprint/template contract changes explicitly.
4. Keep titles and commits focused.

Preferred commit prefixes: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`.

## Good Contribution Targets

- stale documentation and broken command references
- web/shared contract drift
- template, blueprint, parser, or export regressions
- validation and placeholder edge cases
- mobile scaffold cleanup or integration work that is clearly scoped

## Questions

If a change affects blueprint validity, export compatibility, or parser expectations, document the assumption in the PR instead of guessing.
