# Blueprint UI - Installation & Quick Start

## Installation

### 1. Install Python dependencies

**Quick Start (Recommended - uses provided launcher):**

```bash
./run_bpui.sh
# This auto-creates a venv and installs dependencies
```

**Manual Installation:**

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install base dependencies
pip install textual rich tomli-w httpx

# Optional: Install LiteLLM for 100+ providers
pip install litellm
```

### 2. Verify installation

```bash
python test_bpui.py
```

Expected output:

```
=== BPUI Installation Test ===

Testing imports...
✓ bpui
✓ bpui.config
✓ bpui.llm.base
✓ bpui.llm.openai_compat_engine
✓ bpui.llm.litellm_engine (optional)
✓ bpui.prompting
✓ bpui.parse_blocks
✓ bpui.pack_io
✓ bpui.validate
✓ bpui.export
✓ bpui.tui.app

✓ All core modules imported successfully!

...

✓ All tests passed!

You can now run: bpui
```

### 3. Launch the TUI

```bash
bpui
```

## First-time Setup

When you launch `bpui` for the first time:

1. Press **⚙️  Settings** on the home screen
2. Configure your LLM setup:
   - **Engine**: Choose `litellm` or `openai_compatible`
   - **Model**: e.g., `openai/gpt-4` (LiteLLM) or `your-model-name` (OpenAI-compatible)
   - **API Key Env Variable**: e.g., `OPENAI_API_KEY`
   - **Base URL** (OpenAI-compatible only): e.g., `http://localhost:11434/v1`
   - **Temperature**: `0.7` (default)
   - **Max Tokens**: `4096` (default)
3. Press **💾 Save**
4. Press **🔌 Test Connection** to verify

Your settings are saved to `.bpui.toml` in the repo root.

## Quick Start Guide

### Compile a Character (TUI)

1. Launch `bpui`
2. Select **🌱 Compile from Seed**
3. Enter your seed (e.g., "Noir detective with psychic abilities")
4. Choose content mode: Auto / SFW / NSFW / Platform-Safe
5. Press **▶️  Compile**
6. Watch the streaming output
7. Review the 7 generated assets in tabs
8. Press **✓ Validate** to check for errors
9. Press **📦 Export** to export to `output/`

### Generate Seeds (TUI)

1. Launch `bpui`
2. Select **🎲 Seed Generator**
3. Enter genre/theme lines (one per line):

   ```
   Noir detective
   Cyberpunk mercenary
   Fantasy sorceress
   ```

4. Press **✨ Generate Seeds**
5. Click a seed to jump to compilation

### Browse Drafts (TUI)

1. Launch `bpui`
2. Select **📁 Open Drafts**
3. Click a draft to review/validate/export

### Compile a Character (CLI)

```bash
# Basic compilation
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW

# Custom output directory
bpui compile --seed "..." --out custom/dir

# Model override
bpui compile --seed "..." --model openai/gpt-4o
```

### Generate Seeds (CLI)

```bash
# Create input file
echo "Noir detective
Cyberpunk mercenary
Fantasy sorceress" > genres.txt

# Generate seeds
bpui seed-gen --input genres.txt --out "seed output/noir.txt"
```

### Validate (CLI)

```bash
bpui validate drafts/20240203_150000_character_name
bpui validate output/character_name
```

### Export (CLI)

```bash
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4
```

## Common Provider Setups

### OpenAI (LiteLLM)

```toml
engine = "litellm"
model = "openai/gpt-4"
api_key_env = "OPENAI_API_KEY"
```

Set environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic Claude (LiteLLM)

```toml
engine = "litellm"
model = "anthropic/claude-3-opus-20240229"
api_key_env = "ANTHROPIC_API_KEY"
```

Set environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Ollama (OpenAI-compatible)

```toml
engine = "openai_compatible"
model = "llama3.1"
api_key_env = ""
base_url = "http://localhost:11434/v1"
```

No API key needed for local Ollama.

### Local LLM via LM Studio (OpenAI-compatible)

```toml
engine = "openai_compatible"
model = "local-model"
api_key_env = ""
base_url = "http://localhost:1234/v1"
```

### DeepSeek (LiteLLM)

```toml
engine = "litellm"
model = "deepseek/deepseek-chat"
api_key_env = "DEEPSEEK_API_KEY"
```

## Troubleshooting

### "Cannot import 'setuptools.build_backend'" when running pip install

This happens when trying to install with `-e .` outside a virtual environment. **Solutions:**

1. **Use the launcher script (easiest):**

   ```bash
   ./run_bpui.sh
   ```

2. **Or manually activate the venv:**

   ```bash
   source .venv/bin/activate
   pip install textual rich tomli-w httpx
   pip install litellm  # optional
   ```

3. **Or use the venv Python directly:**

   ```bash
   .venv/bin/python -m pip install textual rich tomli-w httpx litellm
   ```

### "LiteLLM not installed"

Install the optional dependency:

```bash
pip install litellm
```

### "Connection failed"

1. Check API key environment variable is set:

   ```bash
   echo $OPENAI_API_KEY  # or your provider's var
   ```

2. For OpenAI-compatible, verify `base_url` is correct
3. Use Settings → Test Connection in the TUI

### "Parse error: Expected 7 asset blocks"

The LLM didn't output the correct format. Try:

- Increasing `max_tokens`
- Using a more capable model
- Simplifying your seed

### "Validation failed"

Check the validation output for:

- Placeholders like `{PLACEHOLDER}`, `((...))`, `{TITLE}`
- Mode mismatches (SFW/NSFW markers)
- User-authorship violations (narrating {{user}} actions/thoughts)

## Next Steps

- Read [bpui/README.md](bpui/README.md) for full documentation
- Check [main README](../README.md) for blueprint details
- See [.github/copilot-instructions.md](../.github/copilot-instructions.md) for generation rules

## Support

For issues:

1. Run `python test_bpui.py` to check installation
2. Check Settings → Test Connection in TUI
3. Review validation output for specific errors
4. Check that blueprints exist in repo root (`rpbotgenerator.md`, etc.)
