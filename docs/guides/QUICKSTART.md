# Blueprint UI - Quick Reference

## Installation (One-Time)

```bash
# Basic (OpenAI-compatible only)
pip install -e .

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

### Compare Characters

```bash
# TUI
bpui → Similarity Analyzer → Select two characters → Compare

# CLI (basic comparison)
bpui similarity "character1" "character2"

# CLI (with LLM deep analysis)
bpui similarity "character1" "character2" --use-llm

# Compare all pairs
bpui similarity drafts --all --use-llm

# Cluster similar characters
bpui similarity drafts --cluster --threshold 0.75
```

## Settings (.bpui.toml)

### OpenAI

```toml
engine = "openai_compatible"
model = "openrouter/openai/gpt-4o-mini"
api_key_env = "OPENROUTER_API_KEY"
base_url = "https://openrouter.ai/api/v1"
```

### Claude

```toml
engine = "openai_compatible"
model = "openrouter/anthropic/claude-3-opus"
api_key_env = "OPENROUTER_API_KEY"
base_url = "https://openrouter.ai/api/v1"
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
# Optional provider SDKs:
pip install openai google-generativeai
```

## File Locations

- Config: `.bpui.toml` (repo root)
- Drafts: `drafts/` (auto-created)
- Exports: `output/<name>(<model>)/`
- Blueprints: `blueprints/` directory with hierarchical structure
  - `blueprints/rpbotgenerator.md` - Main orchestrator
  - `blueprints/system/` - System-level blueprints
  - `blueprints/templates/` - Template-specific blueprints
  - `blueprints/examples/` - Example and alternative blueprints
  - See `blueprints/README.md` for full documentation

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

# Compare characters
bpui similarity "char1" "char2" --use-llm

# Analyze all characters
bpui similarity drafts --all --cluster --threshold 0.75
```

## Support Files

- Full docs: [bpui/README.md](bpui/README.md)
- Installation guide: [INSTALL.md](INSTALL.md)
- Implementation details: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- Feature audit: [docs/FEATURE_AUDIT.md](docs/FEATURE_AUDIT.md)
- Similarity analyzer: [docs/SIMILARITY_ENHANCEMENTS.md](docs/SIMILARITY_ENHANCEMENTS.md)
- Test script: `python test_bpui.py`
