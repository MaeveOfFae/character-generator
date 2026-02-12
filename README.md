# Character Generator (Blueprint Pack)

A comprehensive prompt blueprint system for compiling consistent character assets from a single **SEED**. Includes interactive terminal UI (TUI), graphical UI (GUI), and CLI with keyboard shortcuts, batch operations, and multi-provider LLM support.

## Quick Start

### Option 1: Terminal UI (Recommended)

Launch the interactive TUI with full keyboard navigation:

```bash
# Using provided launcher (recommended - auto-creates venv)
./run_bpui.sh

# Or install manually
source .venv/bin/activate
pip install textual rich tomli-w httpx
pip install litellm  # optional, for 100+ providers
bpui
```

### Option 2: Graphical UI (Qt6)

Launch the modern Qt6-based GUI:

```bash
# Install dependencies
pip install PySide6

# Launch GUI
bpui
```

### Option 3: CLI Mode (Scriptable)

Compile characters from command line for automation:

```bash
# Single character compilation
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW

# Batch compilation from file
bpui batch --input seeds.txt --mode NSFW --continue-on-error

# Generate seeds
bpui seed-gen --input genres.txt --out "seed output/noir.txt"

# Validate a character pack
bpui validate drafts/20240203_150000_character_name

# Export to output directory
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4

# Analyze character similarity
bpui similarity "character1" "character2" --use-llm
```

## Features

### 🎭 Character Generation

- **7-Asset Suite**: Generate system_prompt, post_history, character_sheet, intro_scene, intro_page, a1111_prompt, suno_prompt from a single SEED
- **Strict Hierarchy**: Ensures consistency across all assets
- **Asset Isolation**: Prevents downstream contradictions
- **Deterministic Output**: Reproducible results for the same seed

### 🤖 LLM Integration

- **Multi-Provider Support**: LiteLLM for 100+ providers (OpenAI, Anthropic, DeepSeek, Google, Cohere, Mistral, etc.)
- **OpenAI-Compatible**: Support for local models (Ollama, LM Studio, vLLM, etc.)
- **Provider-Specific API Keys**: Auto-selected based on model
- **Streaming Support**: Real-time generation feedback
- **LLM Chat Assistant**: Interactive refinement in Review screen

### 📊 Similarity Analyzer

- **Character Comparison**: Compare two characters to find commonalities and differences
- **Multi-Dimensional Scoring**: Personality, values, goals, background, conflict/synergy potential
- **LLM-Powered Analysis**: Deep narrative insights, story opportunities, scene suggestions, dialogue styles, relationship arcs
- **Redundancy Detection**: Identify when characters are too similar (low/medium/high/extreme levels)
- **Rework Suggestions**: Actionable ideas to differentiate similar characters
- **Merge Recommendations**: Suggest merging extreme duplicates (>95% similar)
- **Batch Operations**: Compare all pairs or cluster similar characters
- **Triple-Interface Support**: Available in CLI, TUI, and GUI

### 👶 Advanced Features

- **Offspring Generator**: Create child characters from two parents, combining traits and values
- **Seed Generator**: Generate seed lists from genre/theme inputs
- **Draft Index**: Searchable index of all generated characters with filtering
- **Metadata Tracking**: Automatic tracking of generation parameters, lineage, and tags

### 🛠️ Workflow Tools

- **Batch Compilation**: Compile multiple characters from seed files with progress tracking
- **Asset Editing**: Edit and save generated assets with live validation
- **Draft Management**: Browse and review all generated characters
- **Integrated Validation**: Checks for placeholders, mode consistency, user-authorship violations
- **Export Integration**: Creates properly structured output directories with multiple presets

### 🖥️ User Interfaces

**Terminal UI (TUI):**
- Keyboard shortcuts across all screens
- Real-time streaming output
- Draft browser with search
- Interactive LLM chat assistant
- Similarity analyzer with batch operations

**Graphical UI (GUI):**
- Modern Qt6 interface
- Blueprint browser and editor
- Template manager and wizard
- Asset designer for custom assets
- Similarity analyzer widget
- Dependency resolver

**Command Line Interface (CLI):**
- Scriptable commands for automation
- Comprehensive help system
- All TUI features available via CLI flags

### 🎨 Export System

Multiple export presets for different platforms:

- **ChubAI**: Character cards for Chub AI platform
- **TavernAI**: Character info for SillyTavern
- **RisuAI**: Format for Risu character gallery
- **Raw**: Unprocessed character data

### 📝 Moreau Virus / Morphosis Support

- Automatic lore application for furry/anthro/scalie characters
- Functional trait handling (anatomy, clothing, social context)
- Morphosis counterculture integration
- Respects canon constraints (2-year timeline, vaccine, prevalence)

## Documentation

- **Project README**: [README.md](README.md) - This file
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) - Quick reference guide
- **TUI Guide**: [bpui/README.md](bpui/README.md) - TUI documentation and keyboard shortcuts
- **Feature Audit**: [docs/FEATURE_AUDIT.md](docs/FEATURE_AUDIT.md) - Complete feature audit
- **Similarity Analyzer**: [docs/SIMILARITY_ENHANCEMENTS.md](docs/SIMILARITY_ENHANCEMENTS.md) - Detailed documentation
- **API Docs**: Generate with `make docs` and view at `docs/api/bpui/`
- **Documentation Index**: [docs/README.md](docs/README.md) - Navigation hub for all documentation

## Repository Structure

```
character-generator/
├── blueprints/              # All prompt blueprints
│   ├── rpbotgenerator.md       # Main orchestrator
│   ├── examples/               # Example and alternative blueprints
│   │   └── a1111_sdxl_comfyui.md   # SDXL alternate
│   ├── system/                 # System-level blueprints
│   │   ├── offspring_generator.md   # Offspring synthesis
│   │   └── system_prompt.md         # System-level system prompt
│   └── templates/              # Template-specific blueprints
│       ├── example_image_only/   # Image generation template
│       │   ├── a1111.md
│       │   ├── character_sheet.md
│       │   └── post_history.md
│       ├── example_minimal/       # Minimal template (default)
│       │   ├── character_sheet.md
│       │   ├── intro_page.md
│       │   ├── intro_scene.md
│       │   ├── post_history.md
│       │   └── system_prompt.md
│       └── example_music_only/   # Music generation template
│           ├── character_sheet.md
│           ├── post_history.md
│           └── suno.md
├── bpui/                   # Python package
│   ├── cli.py                  # CLI entry point
│   ├── config.py               # Configuration
│   ├── prompting.py            # Blueprint loading
│   ├── similarity.py           # Similarity analyzer
│   ├── parse_blocks.py         # Parser
│   ├── llm/                    # LLM adapters
│   ├── gui/                    # Qt6 GUI
│   └── tui/                    # Textual TUI
├── tools/                   # Shell scripts
│   ├── export_character.sh     # Export helper
│   └── validate_pack.py        # Validation script
├── docs/                    # Documentation
├── output/                  # Exported characters
├── drafts/                  # Generated drafts
└── tests/                   # Test suite
```

## Installation

### Quick Install

```bash
# Clone repository
git clone https://github.com/MaeveOfFae/character-generator.git
cd character-generator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with LiteLLM support (recommended)
pip install -e ".[litellm]"

# Or basic install (OpenAI-compatible only)
pip install -e .
```

### Dependencies

**Required:**
- Python 3.11+
- textual (TUI)
- rich (TUI styling)
- tomli-w (TOML parsing)
- httpx (HTTP client)

**Optional (for LiteLLM):**
- litellm (100+ LLM providers)

**Optional (for GUI):**
- PySide6 (Qt6 bindings)

## Configuration

Configuration is handled via `.bpui.toml` file:

```toml
# LLM Provider
engine = "litellm"  # or "openai_compatible"
model = "openai/gpt-4"
api_key_env = "OPENAI_API_KEY"

# OpenAI-compatible settings
base_url = ""  # e.g., "http://localhost:11434/v1" for Ollama

# Generation settings
temperature = 0.7
max_tokens = 4096
batch_max_concurrent = 5

# Logging
log_level = "INFO"
log_file = ""  # Optional log file path
```

## Usage Examples

### Generate a Character

```bash
# TUI/GUI: Use the interface
# CLI:
bpui compile --seed "Strict museum curator who can't stop watching {{user}}" --mode SFW
```

### Compare Characters

```bash
# Basic comparison
bpui similarity "character1" "character2"

# With LLM deep analysis
bpui similarity "character1" "character2" --use-llm

# Compare all pairs in drafts directory
bpui similarity drafts --all --use-llm

# Cluster similar characters
bpui similarity drafts --cluster --threshold 0.75
```

### Generate Offspring

```bash
bpui offspring \
  --parent1 "Parent1" \
  --parent2 "Parent2" \
  --mode NSFW
```

### Batch Compile

```bash
bpui batch \
  --input seeds.txt \
  --mode NSFW \
  --continue-on-error \
  --max-concurrent 3
```

## SEED Guidelines

Good seeds imply:
- **Power Dynamic**: Who has leverage and why
- **Emotional Temperature**: Tension level of the relationship
- **Tension Axis**: What creates conflict
- **Why {{user}} Matters**: Role, connection, obligation (without asserting user actions)

**Example Seeds:**
- "Street medic with a savior complex, protective toward {{user}}, terrified of abandonment"
- "Moreau (canine) bartender at Morphosis venue, knows everyone's secrets"
- "Corporate fixer: polite menace, offers {{user}} a deal they can't afford to accept"

## Content Modes

- **SFW**: No explicit sexual content; "fade to black" if sexuality implied
- **NSFW**: Explicit content allowed if implied by seed
- **Platform-Safe**: Avoid explicit content and platform-risky extremes

Specify mode in TUI, CLI (`--mode SFW`), or inline in seed (e.g., "Mode: SFW").

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_similarity.py

# With coverage
pytest --cov=bpui tests/
```

## Development

```bash
# Install in development mode
pip install -e .

# Run TUI from source
python -m bpui.cli

# Format code
black bpui/ tests/

# Type checking
mypy bpui/

# Generate API docs
make docs
```

## Contributing

We welcome contributions! Please read:

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines
- [SECURITY.md](SECURITY.md) - Security policy

## License

[BSD 3-Clause License](LICENSE) - See LICENSE file for details

## Support

- **Documentation**: [docs/](docs/) - Complete documentation
- **Issues**: Report bugs at GitHub Issues
- **Discussions**: Use GitHub Discussions for questions

---

*Blueprint Pack Character Generator - Compiling Consistent Characters from Seeds*