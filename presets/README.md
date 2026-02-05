# Export Presets

Export presets define how character assets are formatted and combined for different AI chat platforms.

## Built-in Presets

- **raw.toml**: Default format with separate text files (current behavior)
- **chubai.toml**: Chub AI JSON format
- **risuai.toml**: RisuAI JSON format
- **tavernai.toml**: TavernAI/SillyTavern character card format

## Creating Custom Presets

Create a `.toml` file with the following structure:

```toml
[preset]
name = "My Custom Format"
format = "json"  # or "text" or "combined"
description = "Description of this export format"

# Field mappings: map asset names to target fields
[[fields]]
asset = "character_sheet"
target = "description"
wrapper = "{{char}} is described as:\n\n{{content}}"

[[fields]]
asset = "system_prompt"
target = "personality"

[[fields]]
asset = "intro_scene"
target = "first_message"

[[fields]]
asset = "post_history"
target = "example_dialogues"
wrapper = "Example conversation:\n{{content}}"

# Optional: specify output filename pattern
[output]
filename = "{{character_name}}.json"
# Use these placeholders: {{character_name}}, {{timestamp}}, {{model}}
```

## Field Mappings

The `asset` field should be one of:
- `system_prompt`
- `post_history`
- `character_sheet`
- `intro_scene`
- `intro_page`
- `a1111`
- `suno`

The `target` field depends on your platform's expected format.

## Wrapper Templates

Use `{{content}}` in the wrapper to insert the asset content.
Use `{{char}}` for the character name (extracted from character_sheet).
Use `{{user}}` for the user placeholder.

## Format Types

- **text**: Multiple text files in a directory
- **json**: Single JSON file with nested structure
- **combined**: Single text file with all assets concatenated
