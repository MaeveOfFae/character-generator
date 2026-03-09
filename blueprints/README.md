# Blueprint Directory Organization

This directory contains the orchestrator blueprint, shared asset blueprints, template-specific blueprints, and examples.

## Directory Structure

```text
blueprints/
├── rpbotgenerator.md          # Main orchestrator blueprint
├── system_prompt.md           # Shared system prompt blueprint
├── post_history.md            # Shared post-history blueprint
├── character_sheet.md         # Shared character sheet blueprint
├── intro_scene.md             # Shared intro scene blueprint
├── intro_page.md              # Shared intro page blueprint
├── a1111.md                   # Shared A1111 blueprint
├── templates/                 # Template-specific blueprint directories
│   ├── example_image_only/
│   └── example_minimal/
└── examples/                  # Alternate/example blueprints
```

## Core Blueprints

- **rpbotgenerator.md** - Main orchestrator. Defaults to the official V2/V3 Card asset set and supports template overrides.
- **system_prompt.md** - Shared system prompt blueprint.
- **post_history.md** - Shared relationship-state blueprint.
- **character_sheet.md** - Shared structured character blueprint.
- **intro_scene.md** - Shared interaction opener blueprint.
- **intro_page.md** - Shared Markdown intro page blueprint.
- **a1111.md** - Shared Stable Diffusion/A1111 prompt blueprint.

## Template Blueprints

Each template directory contains a `template.toml` manifest plus any local blueprint files it needs.

### example_minimal

This directory backs the official V2/V3 Card default template. Its asset set is:

- system_prompt
- post_history
- character_sheet
- intro_scene
- intro_page
- a1111

### example_image_only

Template focused on image-generation workflows:

- a1111
- character_sheet
- post_history

## Example Blueprints

Alternative/reference blueprints for specialized use cases:

- **a1111_sdxl_comfyui.md** - SDXL-first modular prompt blueprint compatible with AUTOMATIC1111 and ComfyUI.

## Blueprint Resolution

The template manager resolves blueprint files in this order:

1. Template-local blueprint paths declared in `template.toml`
2. Relative path resolution from the template directory
3. Shared blueprint files under `blueprints/`
4. Example blueprints under `blueprints/examples/`

## Adding New Blueprints

When creating new blueprints:

1. Put shared blueprints at the top level of `blueprints/` when they are reusable across templates.
2. Put template-specific blueprints in `blueprints/templates/{template_name}/`.
3. Define template assets and dependency order in `template.toml`.
4. Reference shared files with relative paths when appropriate.
5. Keep blueprint formats asset-specific instead of normalizing them.
