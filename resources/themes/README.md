# Theme Resources

This directory contains theme-related repository assets.

Today that means a mix of:

- legacy Textual-style `.tcss` theme files
- theme metadata `.toml` files tracked with the repo

These files are useful reference material and may be reused by future surfaces, but the current browser app does not load them directly at runtime.

## Built-in Themes

- `dark.tcss`: Dark reference theme
- `light.tcss`: Light reference theme
- `nyx.tcss`: High-contrast signature theme
- `midnight.tcss`: Deep blue ocean theme with cyan accents
- `ember.tcss`: Warm theme with orange and amber tones
- `mono.tcss`: Clean grayscale theme for minimal distraction
- `forest.tcss`: Natural green theme inspired by woodland twilight
- `solarized_dark.tcss`: Popular Solarized color scheme with reduced eye strain
- `blood_for_the_blood_god.tcss`: Aggressive red-accent theme resource

Additional TOML-only metadata files also exist, including `trans.toml`.

## Current Runtime Status

- Browser theme presets currently live in code and browser storage.
- This directory is not automatically watched or imported by the web app.
- If you want these files to become runtime inputs again, wire that behavior into the app explicitly.

## Working With These Files

1. Copy any built-in `.tcss` file as a starting point
2. Rename it (e.g., `my_theme.tcss`)
3. Edit the color and style rules in the file you copied
4. Add or update any paired `.toml` metadata if the consuming surface expects it

### Notes

- Treat these as repo resources, not automatically active UI configuration.
- Keep naming consistent between `.tcss` and `.toml` files when they represent the same theme.
- Update `resources/README.md` if you add a new user-facing resource category.
