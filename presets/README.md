# Export Presets

This directory stores TOML export preset definitions for character asset bundles.

There are two related realities in the repo today:

- `packages/shared/src/export/presets.ts` contains the shared preset application and formatting helpers.
- The browser app currently exposes three built-in export modes directly in its in-browser API layer: `json`, `text`, and `combined`.

So these preset files are still useful repository assets and reference definitions, but they are not the source of truth for the current browser export picker.

## Built-in Presets

- **raw.toml**: Raw asset-pack layout using per-asset output files
- **chubai.toml**: Chub AI oriented JSON mapping
- **risuai.toml**: RisuAI oriented JSON mapping
- **tavernai.toml**: TavernAI or SillyTavern style character-card mapping

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
optional = true

[metadata]
creator = ""

# Output name pattern
[output]
filename = "{{character_name}}.json"
# Shared formatter expands: {{character_name}}, {{timestamp}}, {{model}}
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

Notes:

- Shared export helpers silently skip assets that are not present in the draft.
- `suno` is valid in preset definitions even though it is not part of the current default V2/V3 browser flow.
- Template-specific assets outside the legacy shared set may require custom handling if you want a preset to support them cleanly.

The `target` field depends on your platform's expected format.

## Wrapper Templates

Use `{{content}}` in the wrapper to insert the asset content.
Use `{{char}}` for the character name (extracted from character_sheet).
Use `{{user}}` for the user placeholder.

## Format Types

- **text**: Multiple text files in a directory
- **json**: Single JSON file with nested structure
- **combined**: Single text file with all assets concatenated

## Current Browser Export Behavior

The shipping browser app currently offers:

- `json`: a JSON file with metadata and assets
- `text`: a plain text export with section headers per asset
- `combined`: a markdown bundle with metadata and all assets

If you update the preset system and expect the browser UI to pick those changes up automatically, that is not true today. Update the browser export layer as well.
