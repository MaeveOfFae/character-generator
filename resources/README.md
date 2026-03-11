# Resources Directory

This directory contains repo-tracked non-code assets and reference files.

## Subdirectories

- **themes/** - theme-related files tracked in the repo, including legacy Textual `.tcss` files and theme metadata `.toml` files

## Current State

The only active subdirectory in the current workspace is `themes/`.

Important distinction:

- The browser app currently uses built-in theme presets defined in code plus browser-stored custom themes.
- The files under `resources/themes/` are repository assets and references; they are not the live source of truth for the current browser runtime.

## Usage Guidelines

When adding resources to this directory:

1. Follow the existing naming conventions
2. Include a README file in each subdirectory explaining the resource's purpose
3. Ensure resources are appropriately licensed
4. Update the main README if resources are user-facing

## Questions?

If you need to add resources but aren't sure where to place them, consult the project maintainers or check the main documentation.
