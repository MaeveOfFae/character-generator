# Testing Live Theme Reload

This note applies to the Python-native interfaces, especially the Textual TUI and the legacy Qt GUI. It does not describe the web app or the Tauri desktop shell.

## Scope

Use this document only when working on live theme switching inside the Python UI stack.

## Current TUI Approach

The Textual app reloads theme CSS at the app level and then refreshes the relevant screen so newly rendered widgets pick up the updated styles.

The important files are:

- `bpui/tui/app.py`
- `bpui/tui/settings.py`
- `bpui/core/theme.py`

## How to Test

### TUI

```bash
./run_bpui.sh tui
```

Then:

1. Open Settings.
2. Change the theme.
3. Save.
4. Confirm the updated styling appears without a full app restart.

### Legacy Qt GUI

```bash
./run_bpui.sh
```

Then:

1. Open Settings or the relevant theme controls.
2. Change the theme or preset.
3. Save.
4. Confirm the new theme is applied to newly refreshed UI state.

## Validation Notes

Useful checks after theme work:

```bash
pytest -m "not slow"
pytest --no-cov tests/unit/test_theme.py
```

## Documentation Note

Because the main product surfaces are now the web app and Tauri desktop shell, this file should stay narrowly focused on the Python-native theme reload behavior.
