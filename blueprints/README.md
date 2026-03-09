# Blueprints

This directory contains the official orchestrator, shared asset blueprints, example blueprints, and template manifests used by the template system.

## Layout

```text
blueprints/
├── rpbotgenerator.md          # Official orchestrator blueprint
├── system_prompt.md           # Shared system_prompt blueprint
├── post_history.md            # Shared post_history blueprint
├── character_sheet.md         # Shared character_sheet blueprint
├── intro_scene.md             # Shared intro_scene blueprint
├── intro_page.md              # Shared intro_page blueprint
├── a1111.md                   # Shared A1111 blueprint
├── examples/                  # Alternate/example blueprints
└── templates/                 # Template manifests and template-local blueprints
```

## Official Default

The built-in official template exposed by `TemplateManager` is `V2/V3 Card`. Its default asset set is:

1. `system_prompt`
2. `post_history`
3. `character_sheet`
4. `intro_scene`
5. `intro_page`
6. `a1111`

`suno` is not part of the current official default.

## Template Manifests

Each template directory contains a `template.toml` manifest describing:

- template name and version
- asset names
- dependency order via `depends_on`
- optional template-local blueprint files

The official example template under `templates/example_minimal/` mirrors the current default card flow.

## Resolution Order

When a template references blueprint files, resolution happens in this order:

1. Template-local path declared in `template.toml`
2. Relative path from the template directory
3. Shared blueprint under `blueprints/`
4. Example blueprint under `blueprints/examples/`

## Editing Rules

- Keep formats asset-specific; do not normalize different asset outputs into one house style
- Respect the dependency chain; downstream assets should not introduce facts upstream assets would need
- Replace placeholders in generated output, but keep placeholder syntax inside blueprint source when the blueprint expects substitution later
- Treat the orchestrator and template manifests as part of the generation contract

## Adding a Template

1. Create `blueprints/templates/<template_name>/template.toml`
2. Declare assets and `depends_on` edges explicitly
3. Add template-local blueprint files only when the shared blueprint is not suitable
4. Keep filenames and output formats aligned with the validator and export flow
