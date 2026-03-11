# Resources Directory

This directory contains repo-tracked non-code assets and reference files.

## Subdirectories

- **themes/** - theme palette metadata `.toml` files tracked in the repo

## Current State

The only active subdirectory in the current workspace is `themes/`.

Important distinction:

- The browser app currently uses built-in theme presets defined in code plus browser-stored custom themes.
- The files under `resources/themes/` are repository assets and references; they are not the live source of truth for the current browser runtime.
- The theme reference library is intentionally broad and includes both utility palettes and faction-inspired presets mirrored by the current web app.

## Usage Guidelines

When adding resources to this directory:

1. Follow the existing naming conventions
2. Include a README file in each subdirectory explaining the resource's purpose
3. Ensure resources are appropriately licensed
4. Update the main README if resources are user-facing

## Questions?

If you need to add resources but aren't sure where to place them, consult the project maintainers or check the main documentation.
