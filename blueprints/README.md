# Blueprint Directory Organization

This directory contains blueprints organized by their purpose and usage.

## Directory Structure

```
blueprints/
├── system/          # System-level and orchestrator blueprints
├── templates/       # Template-specific blueprints
│   ├── example_image_only/
│   ├── example_music_only/
│   └── example_minimal/
└── examples/        # Example and alternative blueprints
```

## System Blueprints (`system/`)

These are core system blueprints that define infrastructure and orchestrator logic.

- **system_prompt.md** - Core system prompt definition for character behavioral logic
- **rpbotgenerator.md** - Main orchestrator for generating complete character suites
- **offspring_generator.md** - Special orchestrator for synthesizing characters from two parents

## Template Blueprints (`templates/`)

Each template directory contains the blueprints specific to that template.

### example_image_only
For generating character visuals with A1111/SDXL prompts:
- a1111.md - Stable Diffusion image prompt blueprint
- character_sheet.md - Structured character data
- post_history.md - Conversation context and relationship state

### example_music_only
For generating character theme songs with Suno:
- suno.md - Suno music generation prompt blueprint
- character_sheet.md - Structured character data
- post_history.md - Conversation context and relationship state

### example_minimal
For simple character generation with narrative elements:
- intro_scene.md - First interaction scenario
- intro_page.md - Visual character introduction page (Markdown)
- character_sheet.md - Structured character data
- post_history.md - Conversation context and relationship state

**Note:** All templates reference system blueprints for common assets like `system_prompt.md`.

## Example Blueprints (`examples/`)

Alternative and example blueprints that can be used as references or for specialized purposes.

- **a1111_sdxl_comfyui.md** - SDXL-first modular prompt blueprint compatible with AUTOMATIC1111 and ComfyUI

## Blueprint Resolution

The template manager resolves blueprint files in the following order:

1. Template's `assets/` directory
2. Relative path resolution (e.g., `../../system/system_prompt.md`)
3. Template-specific blueprint directories (`blueprints/templates/*/`)
4. System directory (`blueprints/system/`)
5. Examples directory (`blueprints/examples/`)
6. Direct path from blueprints root (`blueprints/`)

## Adding New Blueprints

When creating new blueprints:

1. Place system/orchestrator blueprints in `blueprints/system/`
2. Place template-specific blueprints in `blueprints/templates/{template_name}/`
3. Place alternative/example blueprints in `blueprints/examples/`
4. Update template configuration files to reference the correct blueprint paths
5. Use relative paths (e.g., `../../system/system_prompt.md`) to reference system blueprints

## Shared Blueprints

Some blueprints are shared across multiple templates (character_sheet.md, post_history.md). These are copied to each template directory to ensure template isolation and allow for future customization per template.