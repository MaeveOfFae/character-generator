# Copilot instructions — Character Generator (Blueprint Pack)

## What this repo is
- This workspace is primarily **prompt blueprints** (Markdown) for compiling one **SEED** into a consistent suite of character assets.
- The orchestrator is [rpbotgenerator.md](../rpbotgenerator.md). It compiles assets in a strict hierarchy/order into discrete outputs.
- The asset blueprints live at the repo root: [system_prompt.md](../system_prompt.md), [post_history.md](../post_history.md), [character_sheet.md](../character_sheet.md), [intro_scene.md](../intro_scene.md), [intro_page.md](../intro_page.md), [a1111.md](../a1111.md), [suno.md](../suno.md).

## Core generation contract (don’t break it)
- **One asset per codeblock/file**, and **nothing outside** the asset blocks (see [rpbotgenerator.md](../rpbotgenerator.md)).
- **Strict ordering**: system_prompt → post_history → character_sheet → intro_scene → intro_page → a1111 → suno (see [.clinerules/workflows/generate-suite.md](../.clinerules/workflows/generate-suite.md)).
- **Asset isolation**: lower-tier assets may only depend on the seed + higher-tier assets; don’t introduce facts “downstream” that would need to be referenced “upstream”.
- **User-authorship rule**: never narrate or assign actions/thoughts/sensations/decisions/consent to `{{user}}` (enforced across modules).

## Editing conventions (repo hygiene)
- Prefer **minimal diffs**; don’t rename/restructure folders unless explicitly asked (see [.clinerules/70_repo_hygiene.md](../.clinerules/70_repo_hygiene.md)).
- Keep blueprint formats **module-specific**; do not “normalize” formatting across assets.
- Preserve YAML frontmatter fields (`name`, `description`, `invokable`, `version`, etc.). Most modules are aligned to `version: 3.1`; if you change a format spec, update the relevant blueprint(s) and the orchestrator consistently.
- Treat [output/](../output/) and [seed output/](../seed%20output/) as generated artifacts unless the user asks to modify them.

## Module-specific gotchas
- **system_prompt / post_history**: paragraph-only, ≤300 tokens, no headings/lists (see [system_prompt.md](../system_prompt.md), [post_history.md](../post_history.md)).
- **post_history**: if `{{original}}` is present, extend/refine it; never overwrite/negate it.
- **character_sheet**: field order and names are strict; no bracket placeholders left unfilled in generated output (see [character_sheet.md](../character_sheet.md)).
- **intro_page**: blueprint contains many `{PLACEHOLDER}` tokens that must remain in the blueprint; generated output must replace them all and stay self-contained HTML/CSS (see [intro_page.md](../intro_page.md)).
- **a1111**: blueprint uses `((...))` slots; generated output must replace all of them and set `[Content: SFW|NSFW]` to match mode (see [a1111.md](../a1111.md)).
- **suno**: keep the exact `[Control]` block structure and section headers; no `{TITLE}` placeholders left in generated output (see [suno.md](../suno.md)).

## Developer workflows you can run
- Export a generated suite (expects these files in `source_dir`: `system_prompt.txt`, `post_history.txt`, `character_sheet.txt`, `intro_scene.txt`, `intro_page.html`, `a1111_prompt.txt`, `suno_prompt.txt`):
  - `./tools/export_character.sh "Character Name" "source_dir" "llm_model"` (see [tools/export_character.sh](../tools/export_character.sh)).
  - Outputs to `output/<sanitized_name>(<sanitized_model>)/`.
- Validate outputs for common failures (placeholders, mode mismatches, user-authorship violations): follow [.clinerules/workflows/validate-placeholders.md](../.clinerules/workflows/validate-placeholders.md).
