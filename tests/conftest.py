"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from bpui.core.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Temporary config for testing."""
    config_path = tmp_path / ".bpui.toml"
    return Config(config_path)


@pytest.fixture
def sample_seed():
    """Standard test seed."""
    return "Museum curator who watches {{user}} but hates being noticed"


@pytest.fixture
def sample_seed_thin():
    """Thin seed for testing validation."""
    return "A detective"


@pytest.fixture
def sample_seed_moreau():
    """Moreau seed for testing lorebook support."""
    return "Canine Moreau bartender at a Morphosis venue, protective of {{user}}"


@pytest.fixture
def mock_llm_response():
    """Mock LLM output with 7 assets."""
    return """```
You are Maren, a museum collections registrar. Maintain professional boundaries while tracking {{user}}'s movements with careful precision.
```

```
Treat the relationship with {{user}} as professional leverage under strain.
```

```
name: Maren Voss
age: 34
occupation: Museum collections registrar
heritage: German American

Core Concept:
A gatekeeping registrar who wants control more than closeness.
```

```
The afternoon light filtered through the archive windows, casting long shadows across the wooden floor.
```

```markdown
# Maren Voss

A museum registrar who controls access with quiet intensity.
```

```
[Control]
[Title: Museum Silence]
[Content: NSFW]
[Subject: 1girl, solo, museum registrar]
```

```
[Control]
[Title: Archival Quiet]
[Genre: Ambient]
[Mood: Tense, restrained]
```
"""


@pytest.fixture
def mock_llm_response_with_adjustment():
    """Mock LLM output with adjustment note."""
    return """```
Adjustment Note: Seed augmented for clarity.
```

""" + mock_llm_response.__wrapped__()  # Get the actual fixture function


@pytest.fixture
def sample_character_sheet():
    """Sample character sheet for testing."""
    return """name: Test Character
age: 25
occupation: Detective
heritage: American

Core Concept:
A detective investigating crimes.

Appearance:

- Physical features: Tall, dark hair
- Style: Professional suits
"""


@pytest.fixture
def sample_pack_dir(tmp_path):
    """Create a complete sample pack directory."""
    pack_dir = tmp_path / "test_pack"
    pack_dir.mkdir()
    
    # Create all required files
    (pack_dir / "system_prompt.txt").write_text("System prompt content")
    (pack_dir / "post_history.txt").write_text("Post history content")
    (pack_dir / "character_sheet.txt").write_text("name: Test Character\nage: 25")
    (pack_dir / "intro_scene.txt").write_text("Intro scene content")
    (pack_dir / "intro_page.md").write_text("# Test Character\n\nDescription")
    (pack_dir / "a1111_prompt.txt").write_text("[Control]\n[Content: NSFW]\nPrompt")
    (pack_dir / "suno_prompt.txt").write_text("[Control]\n[Title: Test]\nLyrics")
    
    return pack_dir


@pytest.fixture
def incomplete_pack_dir(tmp_path):
    """Create an incomplete pack directory (missing some files)."""
    pack_dir = tmp_path / "incomplete_pack"
    pack_dir.mkdir()
    
    # Only create some files
    (pack_dir / "system_prompt.txt").write_text("System prompt content")
    (pack_dir / "post_history.txt").write_text("Post history content")
    
    return pack_dir
