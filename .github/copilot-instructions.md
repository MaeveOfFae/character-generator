# Copilot instructions — Character Generator (Blueprint Pack)

## What this repo is
- This workspace is primarily **prompt blueprints** (Markdown) for compiling one **SEED** into a consistent suite of character assets.
- The orchestrator is [rpbotgenerator.md](../blueprints/rpbotgenerator.md). It compiles assets in a strict hierarchy/order into discrete outputs.
- The asset blueprints live in the [blueprints/](../blueprints/) folder: [system_prompt.md](../blueprints/system_prompt.md), [post_history.md](../blueprints/post_history.md), [character_sheet.md](../blueprints/character_sheet.md), [intro_scene.md](../blueprints/intro_scene.md), [intro_page.md](../blueprints/intro_page.md), [a1111.md](../blueprints/a1111.md), [suno.md](../blueprints/suno.md).
- **bpui/**: Terminal TUI application for interactive character generation with multi-provider LLM support (see [bpui/README.md](../bpui/README.md)).

## Repository structure
```
character-generator/
├── blueprints/          # All prompt blueprints (orchestrator + asset specs)
├── bpui/                # Terminal UI application (Python package)
├── tools/               # Shell scripts (export, validation)
├── .clinerules/         # Workflow instructions for agents
├── fixtures/            # Test fixtures and sample outputs
├── output/              # Generated character packs
└── chub preset/         # Chub AI preset configurations
```

## Core generation contract (don't break it)
- **One asset per codeblock/file**, and **nothing outside** the asset blocks (see [rpbotgenerator.md](../blueprints/rpbotgenerator.md)).
- **Strict ordering**: system_prompt → post_history → character_sheet → intro_scene → intro_page → a1111 → suno (see [.clinerules/workflows/generate-suite.md](../.clinerules/workflows/generate-suite.md)).
- **Asset isolation**: lower-tier assets may only depend on the seed + higher-tier assets; don’t introduce facts “downstream” that would need to be referenced “upstream”.
- **User-authorship rule**: never narrate or assign actions/thoughts/sensations/decisions/consent to `{{user}}` (enforced across modules).

## Editing conventions (repo hygiene)
- Prefer **minimal diffs**; don’t rename/restructure folders unless explicitly asked (see [.clinerules/70_repo_hygiene.md](../.clinerules/70_repo_hygiene.md)).
- Keep blueprint formats **module-specific**; do not “normalize” formatting across assets.
- Preserve YAML frontmatter fields (`name`, `description`, `invokable`, `version`, etc.). Most modules are aligned to `version: 3.1`; if you change a format spec, update the relevant blueprint(s) and the orchestrator consistently.
- Treat [output/](../output/) and [seed output/](../seed output/) as generated artifacts unless the user asks to modify them.- **Blueprint location**: All blueprints live in `blueprints/` folder; `bpui/prompting.py` loads from there.

## bpui (Terminal TUI) architecture
- **Entry point**: `bpui/cli.py` (argparse) or `run_bpui.sh` (auto-venv launcher)
- **Config**: `.bpui.toml` (TOML format, gitignored) with provider-specific API keys under `[api_keys]`
- **LLM adapters**: Dual system (LiteLLM for 100+ providers, OpenAI-compatible for local models)
- **Key selection**: Automatic based on model prefix (e.g., `openai/gpt-4` uses `api_keys.openai`)
- **Parser**: `bpui/parse_blocks.py` extracts 7 required codeblocks with strict validation
- **Screens**: Home, Compile, Review, Drafts, Settings, Seed Generator, Validate (see `bpui/tui/`)
## Module-specific gotchas
- **system_prompt / post_history**: paragraph-only, ≤300 tokens, no headings/lists (see [system_prompt.md](../blueprints/system_prompt.md), [post_history.md](../blueprints/post_history.md)).
- **post_history**: if `{{original}}` is present, extend/refine it; never overwrite/negate it.
- **character_sheet**: field order and names are strict; no bracket placeholders left unfilled in generated output (see [character_sheet.md](../blueprints/character_sheet.md)).
- **intro_page**: blueprint contains many `{PLACEHOLDER}` tokens that must remain in the blueprint; generated output must replace them all and be a single Markdown snippet (no HTML/CSS) (see [intro_page.md](../blueprints/intro_page.md)).
- **a1111**: blueprint uses `((...))` slots; generated output must replace all of them and set `[Content: SFW|NSFW]` to match mode (see [a1111.md](../blueprints/a1111.md)).
- **suno**: keep the exact `[Control]` block structure and section headers; no `{TITLE}` placeholders left in generated output (see [suno.md](../blueprints/suno.md)).

## Developer workflows you can run
- **Launch TUI**: `./run_bpui.sh` (recommended) or `source .venv/bin/activate && bpui`
- **Configure LLM**: Use Settings screen in TUI or edit `.bpui.toml` directly
  - Provider-specific keys: `[api_keys]` section with `openai = "sk-..."`, `anthropic = "sk-ant-..."`, etc.
  - Model format: `provider/model-name` (e.g., `openai/gpt-4`, `anthropic/claude-3-opus`)
- **Export a generated suite** (expects these files in `source_dir`: `system_prompt.txt`, `post_history.txt`, `character_sheet.txt`, `intro_scene.txt`, `intro_page.md`, `a1111_prompt.txt`, `suno_prompt.txt`; optional: `a1111_sdxl_prompt.txt`):
  - `./tools/export_character.sh "Character Name" "source_dir" "llm_model"` (see [tools/export_character.sh](../tools/export_character.sh)).
  - Outputs to `output/<sanitized_name>(<sanitized_model>)/`.
- **Validate outputs** for common failures (placeholders, mode mismatches, user-authorship violations): follow [.clinerules/workflows/validate-placeholders.md](../.clinerules/workflows/validate-placeholders.md).
- **Generate full suite**: Use TUI Compile screen or follow [.clinerules/workflows/generate-suite.md](../.clinerules/workflows/generate-suite.md) for manual invocation.
