# Theme Resources

This directory contains theme-related repository assets.

Today that means a curated library of theme metadata `.toml` files tracked with the repo.

These files are useful reference material and may be reused by future surfaces, but the current browser app does not load them directly at runtime.

Note: `midnight.toml` is maintained in the same TOML format as the other theme metadata files and should be treated as a reference asset, not a runtime-loaded preset.

## Catalog Scope

- 27 tracked theme metadata files currently live in this directory.
- Core utility palettes cover dark, light, editorial, grayscale, solarized, forest, ember, midnight, and support-focused options.
- The expanded faction-inspired set leans into gothic sci-fi palettes such as `blood_for_the_blood_god.toml`, `silent_king.toml`, `ultramar.toml`, `imperial_fists.toml`, `raven_guard.toml`, `salamanders.toml`, `iron_warriors.toml`, `mechanicus_brass.toml`, `sororitas_rose.toml`, `cadia_stands.toml`, `krieg_ash.toml`, `thousand_sons.toml`, `drukhari_raid.toml`, `ork_waaagh.toml`, `tau_sept.toml`, `tyranid_hive.toml`, `genestealer_cult.toml`, and `golden_throne.toml`.

## Runtime Relationship

- Browser theme presets currently live in code and browser storage.
- The web app now mirrors this broader palette catalog as built-in presets, but it still does so from code rather than by loading these TOML files directly.
- This directory is not automatically watched or imported by the web app.
- If you want these files to become runtime inputs again, wire that behavior into the app explicitly.

## Working With These Files

1. Copy any built-in `.toml` file as a starting point
2. Rename it (e.g., `my_theme.toml`)
3. Edit the color values in the file you copied
4. Keep it aligned with the active browser theme schema if you intend to reuse it in code

### Notes

- Treat these as repo resources, not automatically active UI configuration.
- Update `resources/README.md` if you add a new user-facing resource category.
