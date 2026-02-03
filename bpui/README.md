# Blueprint UI (bpui)

A terminal TUI application for compiling RPBotGenerator character assets.

## Features

- **Terminal UI**: Interactive Textual-based interface with keyboard shortcuts
- **Any LLM Support**: LiteLLM (most providers) or OpenAI-compatible API
- **Streaming Output**: Real-time generation feedback
- **Draft Management**: Save, browse, and review generated assets
- **Asset Editing**: Edit and save changes to generated assets
- **Batch Operations**: Compile multiple seeds in sequence
- **Validation**: Integrated validator for generated packs
- **Export**: Direct integration with export scripts
- **Seed Generator**: Generate seed lists from genre/theme inputs
- **CLI Mode**: Scriptable commands for automation
- **Keyboard Shortcuts**: Fast navigation and actions across all screens

## Keyboard Shortcuts

All screens display available shortcuts in the footer. Press the indicated keys for quick actions:

### Home Screen
- **Q** - Quit application
- **1** - Single Compile
- **2** - Batch Compile
- **3** - Seed Generator
- **4** - Browse Drafts
- **5** - Validate Pack
- **6** - Settings

### Compile Screen
- **Q / Escape** - Back to home
- **Enter** - Start compilation
- **Ctrl+C** - Cancel generation

### Batch Compile Screen
- **Q / Escape** - Back to home
- **L** - Load seeds file
- **Enter** - Start batch
- **Ctrl+C** - Cancel batch

### Review Screen
- **Q / Escape** - Back to home
- **E** - Toggle edit mode
- **Ctrl+S** - Save changes
- **Tab** - Next asset tab

### Settings Screen
- **Q / Escape** - Back to home
- **T** - Test connection
- **Enter** - Save settings

### Drafts Screen
- **Q / Escape** - Back to home
- **Enter** - Open selected draft
- **D** - Delete draft (coming soon)

### Seed Generator Screen
- **Q / Escape** - Back to home
- **Enter** - Generate seeds
- **Ctrl+S** - Save output (coming soon)

### Validate Screen
- **Q / Escape** - Back to home
- **Enter** - Run validation

## Installation

### 1. Install dependencies

**Quick Start (Recommended):**

```bash
# Use the provided launcher script (auto-creates venv)
./run_bpui.sh
```

**Manual Installation:**

```bash
# Create/activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install base dependencies
pip install textual rich tomli-w httpx

# Optional: Install LiteLLM for 100+ providers
pip install litellm
```

### 2. Configure

On first run, configure settings via the TUI or create `.bpui.toml`:

```toml
engine = "litellm"  # or "openai_compatible"
model = "openai/gpt-4"  # or your model
api_key_env = "OPENAI_API_KEY"  # environment variable name
base_url = ""  # only for openai_compatible
temperature = 0.7
max_tokens = 4096
```

### 3. Run

Launch the TUI:

```bash
bpui
# or explicitly:
bpui tui
```

## Usage

### TUI Mode (Interactive)

Launch the terminal UI:

```bash
bpui
```

**Screens:**

1. **Home**: Main menu with all actions
2. **Settings**: Configure engine, model, API keys, etc.
   - Test connection with "Test Connection" button
3. **Seed Generator**: Generate seed lists from genre/theme lines
4. **Compile**: Generate character suite from a single seed
   - Choose content mode (Auto/SFW/NSFW/Platform-Safe)
   - Streams output in real-time
   - Auto-saves to `drafts/`
5. **Batch Compile**: Generate multiple characters from seed file
   - Load seeds from file (one per line)
   - Choose content mode for all seeds
   - Shows progress counter (X/Y completed)
   - Continues on error with summary at end
6. **Review**: View and edit all 7 assets in tabs
   - Toggle edit mode to modify assets
   - Save changes back to files
   - Auto-validates on open
   - Export to `output/`
7. **Drafts**: Browse previously generated drafts
8. **Validate**: Validate any directory

### CLI Mode (Scriptable)

**Compile a character:**

```bash
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW
bpui compile --seed "..." --mode SFW --out custom/dir --model openai/gpt-4
```

**Batch compile:**

```bash
bpui batch --input seeds.txt --mode NSFW
bpui batch --input seeds.txt --continue-on-error --out-dir output_batch/
```

**Generate seeds:**

```bash
bpui seed-gen --input genres.txt --out "seed output/noir.txt"
```

**Validate a pack:**

```bash
bpui validate drafts/20240203_150000_character_name
bpui validate output/character_name
```

**Export a character:**

```bash
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4
```

## Architecture

### Modules

- **bpui/config.py**: Configuration management (`.bpui.toml`)
- **bpui/llm/**: LLM adapters
  - `base.py`: Abstract interface
  - `litellm_engine.py`: LiteLLM adapter (multi-provider)
  - `openai_compat_engine.py`: OpenAI-compatible REST API
- **bpui/prompting.py**: Blueprint loading and prompt construction
- **bpui/parse_blocks.py**: Strict 7-codeblock parser
- **bpui/pack_io.py**: Draft directory management
- **bpui/validate.py**: Validation wrapper (`tools/validate_pack.py`)
- **bpui/export.py**: Export wrapper (`tools/export_character.sh`)
- **bpui/tui/**: Textual screens
  - `app.py`: Main TUI app
  - `home.py`: Home screen
  - `settings.py`: Settings screen
  - `seed_generator.py`: Seed generator screen
  - `compile.py`: Compilation screen
  - `review.py`: Asset review screen
  - `drafts.py`: Draft browser
  - `validate_screen.py`: Validation screen
- **bpui/cli.py**: CLI entry point

### Parser Contract

The parser enforces strict codeblock isolation:

1. Optional first codeblock: `Adjustment Note: ...`
2. Required 7 codeblocks in exact order:
   1. system_prompt → `system_prompt.txt`
   2. post_history → `post_history.txt`
   3. character_sheet → `character_sheet.txt`
   4. intro_scene → `intro_scene.txt`
   5. intro_page → `intro_page.md`
   6. a1111 → `a1111_prompt.txt`
   7. suno → `suno_prompt.txt`

Character name is extracted from `character_sheet` (`name: ...` field).

### LLM Adapters

**LiteLLM** (default):

- Supports 100+ providers via unified API
- Format: `provider/model` (e.g., `openai/gpt-4`, `anthropic/claude-3`)
- Streaming support

**OpenAI-compatible**:

- Direct REST API calls
- Requires `base_url` (e.g., `http://localhost:11434/v1` for Ollama)
- Streaming support

## Output Structure

**Drafts** (`drafts/`):

```
drafts/
  20240203_150000_maren_voss/
    system_prompt.txt
    post_history.txt
    character_sheet.txt
    intro_scene.txt
    intro_page.md
    a1111_prompt.txt
    suno_prompt.txt
```

**Exports** (`output/`):

```
output/
  maren_voss(gpt4)/
    system_prompt.txt
    post_history.txt
    character_sheet.txt
    intro_scene.txt
    intro_page.md
    a1111_prompt.txt
    suno_prompt.txt
```

## Development

**Run from source:**

```bash
python -m bpui.cli
```

**Test a component:**

```python
from bpui.config import Config
from bpui.llm.litellm_engine import LiteLLMEngine

config = Config()
engine = LiteLLMEngine(
    model=config.model,
    api_key=config.api_key,
)

result = await engine.test_connection()
print(result)
```

## Troubleshooting

**LiteLLM not found:**

```bash
pip install litellm
```

**Connection errors:**

1. Check API key environment variable is set
2. Use Settings → Test Connection to diagnose
3. For OpenAI-compatible, verify `base_url` is correct

**Parse errors:**

- Ensure LLM output follows the 7-codeblock format
- Check for missing fence markers (```)
- Verify content mode is respected

**Validation failures:**

- Review output in the Review screen
- Check for placeholders like `{PLACEHOLDER}`, `((...))`, `{TITLE}`
- Ensure mode consistency (SFW/NSFW markers)

## License

Same as parent repository.
