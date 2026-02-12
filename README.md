# Character Generator (Blueprint UI)

A powerful prompt blueprint system for generating consistent, high-quality character assets from a single **SEED**. Features an interactive terminal UI, full CLI automation, multi-provider LLM support, and advanced character analysis tools.

## Table of Contents

- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
- [Similarity Analyzer](#similarity-analyzer)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

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

### Option 2: CLI Mode (Scriptable)

Run commands directly from the terminal for automation:

```bash
# Compile a character
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW

# Analyze character similarity
bpui similarity "character1" "character2" --use-llm

# Generate seeds from genres
bpui seed-gen --input genres.txt --out seeds.txt

# Validate and export
bpui validate drafts/20240203_150000_character_name
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4
```

---

## Key Features

### 🎯 Character Generation

**7-Asset Suite Generation:**
- System prompt (≤300 tokens)
- Post history behavior layer (≤300 tokens)
- Structured character sheet
- Second-person intro scene
- Markdown intro page
- AUTOMATIC1111 image prompt
- Suno V5 song prompt

**Quality Features:**
- Strict hierarchy for consistency
- Asset isolation preventing contradictions
- Deterministic output for reproducibility
- Content mode support (SFW/NSFW/Platform-Safe)

### 🤖 LLM Integration

**Multi-Provider Support:**
- LiteLLM: 100+ providers (OpenAI, Anthropic, DeepSeek, Google, Cohere, Mistral, etc.)
- OpenAI-compatible: Local models (Ollama, LM Studio, vLLM, etc.)
- Provider-specific API keys auto-selection
- Real-time streaming output

### 🎮 User Interfaces

**Terminal UI (TUI):**
- Full keyboard shortcuts across all screens
- Real-time generation progress
- Asset editing with live validation
- LLM chat assistant for conversational refinement
- Draft browser and management

**Qt6 GUI:**
- Modern graphical interface
- Character browsing and review
- Blueprint browser and editor
- Template manager and wizard

**CLI:**
- Scriptable commands for automation
- Batch operations
- All features accessible via command line

### 🔧 Workflow Tools

- **Batch Compilation**: Generate multiple characters from seed files
- **Seed Generator**: Create seed lists from genre/theme inputs
- **Draft Management**: Browse, review, and edit generated characters
- **Validation**: Integrated checker for placeholders and consistency
- **Export Integration**: Properly structured output for multiple platforms
- **Offspring Generator**: Create hybrid characters from two parents

### 📊 Similarity Analyzer

Compare characters to find commonalities, differences, and relationship potential:

- **Basic Comparison**: Multi-dimensional similarity scoring
  - Personality traits overlap
  - Core values alignment
  - Goals and motivation matching
  - Background element analysis
  - Conflict and synergy potential

- **LLM-Powered Deep Analysis** (optional):
  - Narrative dynamics and interaction patterns
  - Story opportunities and plot hooks
  - Scene suggestions with setting and action
  - Dialogue style analysis
  - Relationship arc development

- **Redundancy Detection**:
  - Four-level assessment (low/medium/high/extreme)
  - Specific issue identification
  - Actionable rework suggestions
  - Merge recommendations for extreme duplicates

- **Batch Operations**:
  - Compare all character pairs in a directory
  - Cluster similar characters with configurable thresholds
  - JSON output for integration

### 🌍 Moreau Virus / Morphosis Support

- Automatic lore application for furry/anthro/scalie characters
- Functional trait handling (anatomy, clothing, social context)
- Morphosis counterculture integration
- Respects canon constraints (2-year timeline, vaccine, prevalence)

---

## Documentation

### Core Documentation
- **[docs/README.md](docs/README.md)** - Documentation index and navigation
- **[docs/FEATURE_AUDIT.md](docs/FEATURE_AUDIT.md)** - Complete feature audit report
- **[docs/SIMILARITY_ENHANCEMENTS.md](docs/SIMILARITY_ENHANCEMENTS.md)** - Similarity analyzer documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference guide

### Guides
- **[bpui/README.md](bpui/README.md)** - Complete TUI documentation
- **[bpui/docs/INSTALL.md](bpui/docs/INSTALL.md)** - Installation guide
- **[bpui/docs/IMPLEMENTATION.md](bpui/docs/IMPLEMENTATION.md)** - Implementation details

### API Documentation
- Generate with: `make docs`
- View at: `docs/api/bpui/`

### Genre Guide
The README includes a comprehensive genre quickstart defining:
- Core genre presets (Romance, Thriller, Horror, Fantasy, Sci-Fi, Comedy)
- Cross-genre structural systems
- Design principles for consistent storytelling

---

## Installation

### Quick Installation

```bash
# Clone repository
git clone https://github.com/MaeveOfFae/character-generator.git
cd character-generator

# Using launcher script (recommended)
./run_bpui.sh

# Manual installation
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Optional Dependencies

```bash
# For LiteLLM (100+ providers)
pip install litellm

# For GUI (Qt6)
pip install PySide6

# For TUI
pip install textual rich tomli-w httpx
```

### Verification

```bash
# Run TUI
bpui

# Run GUI
bpui gui

# Test connection
bpui --help
```

---

## Usage

### Generate a Character

**TUI:**
```
bpui → Compile from Seed → Enter seed → Choose mode → Compile
```

**CLI:**
```bash
bpui compile --seed "Your seed here" --mode NSFW
```

### Seed Examples

Good seeds imply power dynamic, emotional temperature, tension axis, and relationship:

- "Strict museum curator who hates being noticed, but can't stop watching {{user}}"
- "Street medic with a savior complex, protective toward {{user}}, terrified of abandonment"
- "Corporate fixer: polite menace, offers {{user}} a deal they can't afford to accept"
- "Moreau (canine) bartender at Morphosis venue, knows everyone's secrets, protective of {{user}}"
- "Exhausted single parent, attracted to {{user}}, guilt about wanting something for themselves"

### Batch Operations

```bash
# Compile multiple characters
bpui batch --input seeds.txt --mode NSFW --continue-on-error

# Generate seeds
echo "Noir\nCyberpunk\nFantasy" > genres.txt
bpui seed-gen --input genres.txt --out seeds.txt
```

### Draft Management

```bash
# Browse drafts
bpui → Open Drafts → Select draft → Review/Edit

# Validate
bpui validate drafts/20240203_150000_character_name

# Export
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4
```

---

## Similarity Analyzer

The similarity analyzer helps you understand relationships between characters and identify redundancy.

### Basic Comparison

```bash
# Compare two characters
bpui similarity "character1" "character2"

# With similarity threshold clustering
bpui similarity drafts --cluster --threshold 0.75
```

### LLM-Powered Analysis

```bash
# Enable deep narrative analysis
bpui similarity "character1" "character2" --use-llm

# Analyze all pairs with LLM
bpui similarity drafts --all --use-llm
```

### Redundancy Detection

The analyzer identifies four levels of character redundancy:

| Level | Score | Action |
|--------|--------|--------|
| **Low** | <75% | No action needed |
| **Medium** | 75-85% | Optional differentiation |
| **High** | 85-95% | Recommended rework |
| **Extreme** | >95% | Consider merging |

**Outputs include:**
- Redundancy score with visual indicator
- Specific issues detected (overlapping traits, values, backgrounds)
- Rework suggestions for each character
- Merge recommendations (extreme only)
- Uniqueness score

### Batch Analysis

```bash
# Compare all pairs in drafts directory
bpui similarity drafts --all --use-llm

# JSON output for integration
bpui similarity "char1" "char2" --use-llm --format json
```

See [docs/SIMILARITY_ENHANCEMENTS.md](docs/SIMILARITY_ENHANCEMENTS.md) for complete documentation.

---

## Configuration

### Settings File

Create `.bpui.toml` in the project root:

```toml
[llm]
engine = "litellm"  # or "openai_compatible"
model = "openai/gpt-4"
api_key_env = "OPENAI_API_KEY"
base_url = ""  # only for openai_compatible

[generation]
temperature = 0.7
max_tokens = 4096

[batch]
max_concurrent = 3
rate_limit_delay = 1.0
```

### Provider Examples

**OpenAI:**
```toml
engine = "litellm"
model = "openai/gpt-4"
api_key_env = "OPENAI_API_KEY"
```

**Anthropic Claude:**
```toml
engine = "litellm"
model = "anthropic/claude-3-opus-20240229"
api_key_env = "ANTHROPIC_API_KEY"
```

**Ollama (Local):**
```toml
engine = "openai_compatible"
model = "llama3.1"
base_url = "http://localhost:11434/v1"
```

---

## Repository Structure

```
character-generator/
├── blueprints/              # Prompt blueprints
│   ├── rpbotgenerator.md        # Main orchestrator
│   ├── system_prompt.md         # System prompt template
│   ├── character_sheet.md      # Character structure
│   ├── intro_scene.md          # Opening scene
│   ├── intro_page.md           # Markdown intro
│   ├── a1111.md               # Image prompt
│   └── suno.md                 # Song prompt
├── bpui/                   # Core application
│   ├── cli.py                # CLI entry point
│   ├── config.py             # Configuration
│   ├── similarity.py          # Similarity analyzer
│   ├── prompting.py          # Blueprint loading
│   ├── parse_blocks.py        # Parser
│   ├── llm/                  # LLM adapters
│   ├── tui/                  # Terminal UI
│   └── gui/                  # Qt6 GUI
├── tools/                  # Shell scripts
├── docs/                   # Documentation
├── tests/                  # Test suite
├── drafts/                 # Auto-saved drafts
└── output/                 # Exported characters
```

---

## Contributing

We welcome contributions! Please read:

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Code of conduct
- [SECURITY.md](SECURITY.md) - Security policy

### Development

```bash
# Install in development mode
pip install -e ".[litellm,gui]"

# Run tests
pytest

# Run with coverage
pytest --cov=bpui tests/

# Format code
black bpui/ tests/

# Type checking
mypy bpui/
```

---

## Troubleshooting

### Common Issues

**Can't connect to LLM:**
1. Check API key in Settings or environment variable
2. Use "Test Connection" in Settings
3. Verify base_url for OpenAI-compatible providers
4. Ensure model name matches provider format

**Parse errors:**
- Increase max_tokens in Settings
- Try a more capable model
- Simplify seed

**Import errors:**
```bash
pip install textual rich tomli-w httpx
pip install litellm  # for LLM support
pip install PySide6  # for GUI
```

---

## License

This project is licensed under the same terms as the parent repository.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/MaeveOfFae/character-generator/issues)
- **Documentation**: [docs/README.md](docs/README.md)
- **Quick Reference**: [QUICKSTART.md](QUICKSTART.md)