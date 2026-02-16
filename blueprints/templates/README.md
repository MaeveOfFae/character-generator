# Blueprint Templates

This directory contains built-in template blueprints for different character generation scenarios.

## Template Structure

Each template is a self-contained directory with:
- `template.toml` - Template configuration and metadata
- `assets/` - Associated assets and resources
- Blueprint .md files - Character asset prompts

## Available Templates

### example_minimal
The default minimal template generating all 7 standard character assets:
- system_prompt
- character_sheet
- intro_scene
- intro_page
- post_history
- a1111_prompt
- suno_prompt

### example_image_only
Template focused on image generation assets:
- a1111_prompt (Stable Diffusion)
- character_sheet
- post_history

### example_music_only
Template focused on music generation assets:
- suno_prompt
- character_sheet
- post_history

## Custom Templates

Users can create custom templates by:
1. Copying an existing template directory
2. Modifying the `template.toml` file
3. Adding/editing blueprint .md files
4. Including any necessary assets

See the main documentation for detailed template creation guides.