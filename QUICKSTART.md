# Blueprint UI - Quick Reference

## Installation (One-Time)

```bash
# Basic (OpenAI-compatible only)
pip install -e .

# Recommended (with LiteLLM)
pip install -e ".[litellm]"

# Verify
python test_bpui.py
```

## Launch

```bash
# Interactive TUI
bpui

# Or with launcher script
./run_bpui.sh

# CLI help
bpui --help
```

## Common Workflows

### First Time Setup

1. Launch `bpui`
2. Go to ⚙️  Settings
3. Configure engine, model, API key
4. Test Connection
5. Save

### Generate a Character

```bash
# TUI
bpui → Compile from Seed → Enter seed → Choose mode → Compile

# CLI
bpui compile --seed "Your seed here" --mode NSFW
```

### Generate Seeds

```bash
# TUI
bpui → Seed Generator → Enter genres → Generate → Click seed to compile

# CLI
echo "Genre 1\nGenre 2" > genres.txt
bpui seed-gen --input genres.txt --out seeds.txt
```

### Review/Export

```bash
# TUI
bpui → Open Drafts → Select draft → Validate → Export

# CLI
bpui validate drafts/20240203_150000_character_name
bpui export "Character Name" drafts/20240203_150000_character_name
```

## Settings (.bpui.toml)

### OpenAI

```toml
engine = "litellm"
model = "openai/gpt-4"
api_key_env = "OPENAI_API_KEY"
```

### Claude

```toml
engine = "litellm"
model = "anthropic/claude-3-opus-20240229"
api_key_env = "ANTHROPIC_API_KEY"
```

### Ollama (Local)

```toml
engine = "openai_compatible"
model = "llama3.1"
base_url = "http://localhost:11434/v1"
```

## Keyboard Shortcuts (TUI)

- `q` - Quit
- `h` - Home screen
- `Tab` - Navigate widgets
- `Enter` - Activate button/select item
- `Esc` - Cancel/Back

## Troubleshooting

### Can't connect to LLM

1. Add your API key in Settings screen (provider-specific field)
   - Or check environment variable: `echo $OPENAI_API_KEY`
2. Settings → Test Connection
3. Verify base_url (if using OpenAI-compatible)
4. Ensure model name matches provider (e.g., `openai/gpt-4` uses OpenAI key)

### Parse errors

- Increase max_tokens in Settings
- Try a more capable model
- Simplify seed

### Import errors

```bash
pip install textual rich tomli-w httpx
# For LiteLLM:
pip install litellm
```

## File Locations

- Config: `.bpui.toml` (repo root)
- Drafts: `drafts/` (auto-created)
- Exports: `output/<name>(<model>)/`
- Blueprints: `rpbotgenerator.md`, etc. (repo root)

## CLI Quick Commands

```bash
# Compile
bpui compile --seed "detective" --mode SFW

# Generate seeds
bpui seed-gen --input genres.txt --out seeds.txt

# Validate
bpui validate output/character_name

# Export
bpui export "Name" drafts/20240203_150000_name --model gpt4
```

## Support Files

- Full docs: [bpui/README.md](bpui/README.md)
- Installation guide: [INSTALL.md](INSTALL.md)
- Implementation details: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- Test script: `python test_bpui.py`
