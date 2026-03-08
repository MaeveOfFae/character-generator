# Character Generator (Blueprint Pack)

A comprehensive prompt blueprint system for compiling consistent character assets from a single **SEED**. Features modern web, mobile, and desktop UIs with full API backend.

## Quick Start

### Option 1: Web UI (Recommended)

Modern React-based web interface with mobile support:

```bash
# Install dependencies
pnpm install

# Start API server (terminal 1)
python -m uvicorn bpui.api.main:app --reload

# Start web dev server (terminal 2)
pnpm dev:web

# Open http://localhost:3000
# API docs at http://localhost:8000/docs
```

### Option 2: Mobile App (React Native + Expo)

```bash
# Start Expo development server
pnpm dev:mobile

# Press 'w' for web, 'i' for iOS, 'a' for Android
```

### Option 3: Desktop App (Tauri)

> **Note:** Desktop app is in development. Currently a placeholder.

```bash
# Requires Rust installation first
pnpm tauri:dev
```

### Option 4: Terminal UI (TUI)

Classic terminal interface with keyboard navigation:

```bash
./run_bpui.sh
# or
bpui tui
```

### Option 5: CLI Mode (Scriptable)

```bash
# Single character compilation
bpui compile --seed "Noir detective with psychic abilities" --mode NSFW

# Batch compilation
bpui batch --input seeds.txt --mode NSFW --continue-on-error

# Generate seeds
bpui seed-gen --input genres.txt --out "seed-output/noir.txt"
bpui validate drafts/20240203_150000_character_name

# Export to output directory
bpui export "Character Name" drafts/20240203_150000_character_name --model gpt4

# Analyze character similarity
bpui similarity "character1" "character2" --use-llm
```

## Architecture

```
character-generator/
├── packages/
│   ├── shared/          # Shared TypeScript (types, API client)
│   ├── web/             # React + Vite web app
│   ├── mobile/          # React Native + Expo mobile app
│   └── desktop/         # Tauri desktop wrapper
├── bpui/
│   ├── api/             # FastAPI backend
│   ├── core/            # Core logic (config, prompting, parsing)
│   ├── llm/             # LLM engine integrations
│   ├── features/        # Feature modules (templates, export, similarity)
│   ├── tui/             # Terminal UI (Textual)
│   └── gui/             # Qt6 GUI (PySide6)
├── blueprints/          # Blueprint templates
├── presets/             # Export presets
└── drafts/              # Generated characters
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET/POST | Configuration management |
| `/api/config/test` | POST | Test API connection |
| `/api/models/{provider}` | GET | List available models |
| `/api/templates` | GET/POST | Template CRUD |
| `/api/generate/single` | POST (SSE) | Generate character |
| `/api/generate/batch` | POST (SSE) | Batch generation |
| `/api/drafts` | GET | List drafts |
| `/api/drafts/{id}` | GET/DELETE | Get/delete draft |
| `/api/similarity` | POST | Compare characters |
| `/api/offspring` | POST (SSE) | Generate offspring |
| `/api/export` | POST | Export with preset |
| `/api/chat` | POST (SSE) | Chat-based refinement |

## Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# Development mode with hot reload
docker-compose --profile dev up
```

## Features

### 🎭 Character Generation

- **7-Asset Suite**: Generate system_prompt, post_history, character_sheet, intro_scene, intro_page, a1111_prompt, suno_prompt from a single SEED
- **Strict Hierarchy**: Ensures consistency across all assets
- **Asset Isolation**: Prevents downstream contradictions
- **Deterministic Output**: Reproducible results for the same seed

### 🤖 LLM Integration

- **OpenRouter Integration**: Unified access to multiple AI models through OpenRouter API
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

- **Documentation Index**: [docs/README.md](docs/README.md) - Complete navigation hub for all documentation
- **Quick Start**: [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md) - Fast-track getting started guide
- **TUI Guide**: [bpui/README.md](bpui/README.md) - TUI documentation and keyboard shortcuts
- **Feature Documentation**: [docs/features/](docs/features/) - Detailed feature guides and audits
- **Similarity Analyzer**: [docs/guides/SIMILARITY_ENHANCEMENTS.md](docs/guides/SIMILARITY_ENHANCEMENTS.md) - Deep dive into character comparison
- **OpenRouter Support**: [docs/guides/OPENROUTER_SUPPORT.md](docs/guides/OPENROUTER_SUPPORT.md) - Using OpenRouter with 100+ models
- **API Docs**: [docs/api/](docs/api/) - API reference documentation
- **Installation**: [docs/installation/](docs/installation/) - Installation guides and platform notes
- **Development**: [docs/development/](docs/development/) - Developer and contributor documentation
- **Archive**: [docs/archive/](docs/archive/) - Historical documentation and implementation notes

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
│       └── example_minimal/       # Minimal template (default)
│           ├── character_sheet.md
│           ├── intro_page.md
│           ├── intro_scene.md
│           ├── post_history.md
│           └── system_prompt.md
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

# Install package
pip install -e .
```

### Dependencies

**Required:**
- Python 3.11+
- textual (TUI)
- rich (TUI styling)
- tomli-w (TOML parsing)
- httpx (HTTP client)

**Optional (for GUI):**
- PySide6 (Qt6 bindings)

## Configuration

Configuration is handled via `.bpui.toml` file:

```toml
# LLM Provider
engine = "openai_compatible"
model = "openrouter/openai/gpt-4o-mini"

# API Keys
[api_keys]
openai = "sk-..."
openrouter = "sk-or-v1-..."  # For OpenRouter models
anthropic = "sk-ant-..."     # For Anthropic direct access

# OpenAI-compatible settings
base_url = "https://openrouter.ai/api/v1"  # or e.g., "http://localhost:11434/v1" for Ollama

# Generation settings
temperature = 0.7
max_tokens = 4096
batch_max_concurrent = 5

# Logging
log_level = "INFO"
log_file = ""  # Optional log file path
```

**Presets Available:**
- `presets/openrouter.toml` - Preconfigured for OpenRouter models
- `presets/chubai.toml` - ChubAI format preset
- `presets/risuai.toml` - RisuAI format preset
- `presets/tavernai.toml` - TavernAI format preset

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