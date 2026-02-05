# Contributing to Character Generator

Thank you for your interest in contributing to Character Generator! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Blueprint Development](#blueprint-development)
- [Questions?](#questions)

## Getting Started

### Prerequisites

- Python 3.10+ (3.11+ recommended)
- Git
- A text editor or IDE (VS Code recommended)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/character-generator.git
   cd character-generator
   ```

## Development Setup

### Quick Setup (Recommended)

```bash
# Auto-creates venv and installs dependencies
./run_bpui.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt
```

### Verify Setup

```bash
# Run fast tests
make test-fast

# Or manually
pytest -m "not slow"
```

## Code Style

### Python

- **Follow PEP 8** style guidelines
- **Use type hints** for function parameters and return values
- **Write docstrings** for public functions (Google style)
- **Maximum line length**: 100 characters
- **Format with Black** (optional but encouraged)

Example:
```python
def create_asset(name: str, content: str, mode: Optional[str] = None) -> dict:
    """Create a new character asset.
    
    Args:
        name: Asset name (e.g., "system_prompt")
        content: Asset content
        mode: Content mode (SFW/NSFW/Platform-Safe)
    
    Returns:
        Dict containing asset metadata
    """
    pass
```

### Blueprint Files

- YAML frontmatter required (`name`, `description`, `version`)
- Markdown formatting
- Follow hierarchy rules (higher-tier assets don't depend on lower-tier)
- Keep format specifications exact (don't "normalize" across assets)

## Testing

### Test Requirements

- New features **must** have tests
- Maintain **≥80% coverage** (enforced by pytest)
- Integration tests marked with `@pytest.mark.slow`

### Running Tests

```bash
# All tests with coverage
make test

# Fast tests only (recommended for development)
make test-fast

# Specific test file
pytest tests/unit/test_metadata.py -v

# Specific test
pytest tests/unit/test_metadata.py::test_metadata_creation -v

# With coverage report
make test-coverage
```

### Writing Tests

```python
import pytest
from bpui.your_module import your_function


def test_your_function_basic():
    """Test basic functionality."""
    result = your_function("input")
    assert result == "expected"


def test_your_function_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        your_function(None)


@pytest.mark.slow
async def test_your_async_function():
    """Test async functionality (integration test)."""
    result = await your_async_function()
    assert result is not None
```

## Making Changes

### Branch Naming

Create a descriptive branch:
```bash
git checkout -b feat/single-asset-regeneration
git checkout -b fix/parser-unicode-bug
git checkout -b docs/update-quickstart
```

### Commit Messages

Follow conventional commits format:

```
<type>: <short description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code restructuring without behavior change
- `perf`: Performance improvement
- `chore`: Maintenance tasks

Examples:
```
feat: add single asset regeneration to Review screen

Implements Ctrl+R keyboard shortcut and regenerate button.
Uses original seed from draft metadata.

Closes #42

---

fix: handle missing seed in metadata gracefully

When metadata.seed is "unknown", show clear error message
instead of attempting regeneration.

---

docs: update README with Phase 1 features
```

## Pull Request Process

### Before Submitting

1. **Run tests**: `make test-fast`
2. **Check coverage**: Ensure new code is tested
3. **Update documentation**: If adding features, update relevant docs
4. **Run migration if needed**: `make migrate-drafts`
5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   git push origin feat/awesome-feature
   ```

### Submitting PR

1. Go to GitHub and create a Pull Request
2. Fill out the PR template:
   - **Description**: What does this PR do?
   - **Type of Change**: Bug fix, feature, docs, etc.
   - **Checklist**: Tests added, docs updated, etc.
   - **Related Issues**: Link to issues this fixes

3. Wait for review and address feedback
4. Once approved, your PR will be merged!

### PR Review Checklist

Reviewers will check:
- [ ] Tests pass (`make test`)
- [ ] Coverage maintained (≥80%)
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention
- [ ] No breaking changes (or properly documented)

## Blueprint Development

### Blueprint Structure

```markdown
---
name: Asset Name
description: Brief description
invokable: true/false
version: 3.1
---

# Blueprint Content

Instructions for the LLM...
```

### Blueprint Rules

1. **Hierarchy enforcement**: Lower-tier assets only depend on SEED + higher-tier assets
2. **Format specificity**: Each asset has unique formatting (don't normalize)
3. **No placeholders**: Generated output must replace all `{PLACEHOLDER}` tokens
4. **Complete structures**: A1111/Suno require full `[Control]` blocks

### Testing Blueprints

```bash
# Test with single seed
bpui compile --seed "Your test character" --mode NSFW

# Validate output
bpui validate drafts/YYYYMMDD_HHMMSS_character_name
```

## Project Structure

```
character-generator/
├── bpui/              # Python package
│   ├── cli.py         # CLI entry point
│   ├── config.py      # Configuration management
│   ├── metadata.py    # Draft metadata system
│   ├── batch_state.py # Batch resume state
│   ├── prompting.py   # Blueprint loading
│   ├── parse_blocks.py# Output parser
│   ├── pack_io.py     # Draft I/O
│   ├── validate.py    # Pack validation
│   ├── export.py      # Character export
│   ├── llm/           # LLM adapters
│   └── tui/           # Terminal UI
├── blueprints/        # Asset templates
├── tools/             # Scripts
├── tests/             # Test suite
│   ├── unit/          # Fast unit tests
│   └── integration/   # Slow integration tests
└── docs/              # Documentation
```

## Common Tasks

### Adding a New Asset Type

1. Create blueprint in `blueprints/your_asset.md`
2. Add to `parse_blocks.py` ASSET_ORDER and ASSET_FILENAMES
3. Update orchestrator in `blueprints/rpbotgenerator.md`
4. Add TextArea to Review screen
5. Add validation rules to `validate.py`
6. Write tests

### Adding a New LLM Provider

1. Create adapter in `bpui/llm/your_provider.py`
2. Implement `LLMEngine` interface from `bpui/llm/base.py`
3. Add provider detection to `config.py`
4. Add tests
5. Update documentation

### Modifying Parser Logic

1. Update `bpui/parse_blocks.py`
2. Add/update tests in `tests/unit/test_parse_blocks.py`
3. Test with real LLM output
4. Validate against edge cases (extra whitespace, Unicode, etc.)

## Questions?

- **Issues**: Open an issue with the "question" label
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check `bpui/README.md` and `QUICKSTART.md`

## License

By contributing, you agree that your contributions will be licensed under the project's license (see LICENSE file).

---

**Happy coding! 🚀**
