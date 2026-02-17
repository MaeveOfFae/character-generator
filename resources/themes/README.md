# TUI Themes

This directory contains Textual CSS (`.tcss`) theme files for the Blueprint UI terminal interface.

## Built-in Themes

| Theme | File | Description |
|-------|------|-------------|
| **Dark** | `dark.tcss` | Default dark theme with purple accents |
| **Light** | `light.tcss` | Clean light theme for bright environments |
| **Nyx** | `nyx.tcss` | Deep purple and magenta — the blueprint architect's choice |

## Creating Custom Themes

1. Copy any built-in `.tcss` file as a starting point
2. Rename it (e.g., `my_theme.tcss`)
3. Edit the CSS rules — all color references use Textual CSS variables (`$primary`, `$surface`, etc.)
4. The theme will automatically appear in the TUI Settings → Theme picker

### Available CSS Variables

These variables are set by the app based on the theme's `ThemeColors` definition in `bpui/core/theme.py`:

| Variable | Purpose |
|----------|---------|
| `$primary` | Primary accent color (borders, titles) |
| `$secondary` | Secondary accent color |
| `$surface` | Main background color |
| `$panel` | Dialog/panel background color |
| `$warning` | Warning indicators |
| `$error` | Error text color |
| `$success` | Success text color |
| `$accent` | Accent highlights |
| `$text` | Primary text color |
| `$text-muted` | Subdued text color |

### Theme File Structure

Each `.tcss` file contains all screen styles organized by section:

```
Screen (global)
├── HomeScreen
├── SettingsScreen
├── CompileScreen
├── ReviewScreen + dialogs
├── DraftsScreen + DeleteConfirmScreen
├── BatchScreen
├── OffspringScreen + ParentSelectScreen
├── SeedGeneratorScreen
├── SimilarityScreen
└── ValidateScreen
```

### Tips

- Keep layout rules (widths, heights, layouts) consistent across themes
- Only vary color-related properties between themes
- Test your theme with `bpui` → Settings → Theme → select your theme name
- Theme name is derived from the filename stem (e.g., `my_theme.tcss` → "my_theme")
