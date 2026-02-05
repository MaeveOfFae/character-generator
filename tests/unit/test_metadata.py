"""Tests for metadata module."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from bpui.metadata import DraftMetadata


def test_metadata_creation():
    """Test basic metadata creation."""
    metadata = DraftMetadata(seed="Test character")
    
    assert metadata.seed == "Test character"
    assert metadata.mode is None
    assert metadata.model is None
    assert metadata.created is not None
    assert metadata.modified is not None
    assert metadata.tags == []
    assert metadata.favorite is False


def test_metadata_with_all_fields():
    """Test metadata with all fields populated."""
    metadata = DraftMetadata(
        seed="Knight character",
        mode="NSFW",
        model="openai/gpt-4",
        tags=["fantasy", "knight"],
        genre="fantasy",
        notes="Test notes",
        favorite=True,
        character_name="Sir Roland"
    )
    
    assert metadata.seed == "Knight character"
    assert metadata.mode == "NSFW"
    assert metadata.model == "openai/gpt-4"
    assert metadata.tags == ["fantasy", "knight"]
    assert metadata.genre == "fantasy"
    assert metadata.notes == "Test notes"
    assert metadata.favorite is True
    assert metadata.character_name == "Sir Roland"


def test_metadata_to_dict():
    """Test converting metadata to dictionary."""
    metadata = DraftMetadata(
        seed="Test",
        mode="SFW",
        model="test-model"
    )
    
    data = metadata.to_dict()
    
    assert isinstance(data, dict)
    assert data["seed"] == "Test"
    assert data["mode"] == "SFW"
    assert data["model"] == "test-model"
    assert "created" in data
    assert "modified" in data


def test_metadata_from_dict():
    """Test creating metadata from dictionary."""
    data = {
        "seed": "Test character",
        "mode": "NSFW",
        "model": "gpt-4",
        "created": "2026-02-05T10:30:00",
        "modified": "2026-02-05T11:00:00",
        "tags": ["test"],
        "genre": "scifi",
        "notes": "Test",
        "favorite": False,
        "character_name": "Test"
    }
    
    metadata = DraftMetadata.from_dict(data)
    
    assert metadata.seed == "Test character"
    assert metadata.mode == "NSFW"
    assert metadata.model == "gpt-4"
    assert metadata.created == "2026-02-05T10:30:00"
    assert metadata.modified == "2026-02-05T11:00:00"


def test_metadata_save_and_load(tmp_path):
    """Test saving and loading metadata."""
    draft_dir = tmp_path / "test_draft"
    draft_dir.mkdir()
    
    # Create and save metadata
    original = DraftMetadata(
        seed="Test seed",
        mode="SFW",
        model="test-model",
        tags=["tag1", "tag2"],
        character_name="Test Character"
    )
    original.save(draft_dir)
    
    # Check file exists
    metadata_file = draft_dir / ".metadata.json"
    assert metadata_file.exists()
    
    # Load and verify
    loaded = DraftMetadata.load(draft_dir)
    assert loaded is not None
    assert loaded.seed == "Test seed"
    assert loaded.mode == "SFW"
    assert loaded.model == "test-model"
    assert loaded.tags == ["tag1", "tag2"]
    assert loaded.character_name == "Test Character"


def test_metadata_load_missing(tmp_path):
    """Test loading metadata from directory without metadata."""
    draft_dir = tmp_path / "no_metadata"
    draft_dir.mkdir()
    
    metadata = DraftMetadata.load(draft_dir)
    assert metadata is None


def test_metadata_load_invalid_json(tmp_path):
    """Test loading metadata with invalid JSON."""
    draft_dir = tmp_path / "bad_metadata"
    draft_dir.mkdir()
    
    # Write invalid JSON
    metadata_file = draft_dir / ".metadata.json"
    metadata_file.write_text("{ invalid json }")
    
    metadata = DraftMetadata.load(draft_dir)
    assert metadata is None


def test_metadata_create_default(tmp_path):
    """Test creating default metadata from directory."""
    # Create draft directory with timestamp format
    draft_dir = tmp_path / "20260205_103045_test_character"
    draft_dir.mkdir()
    
    # Create some asset files
    (draft_dir / "character_sheet.txt").write_text("Test content")
    (draft_dir / "system_prompt.txt").write_text("Test prompt")
    
    # Create default metadata
    metadata = DraftMetadata.create_default(draft_dir)
    
    assert metadata.seed == "unknown"
    assert metadata.mode is None
    assert metadata.model is None
    assert metadata.character_name == "test_character"
    assert metadata.created is not None
    assert metadata.modified is not None


def test_metadata_create_default_simple_name(tmp_path):
    """Test creating default metadata with simple directory name."""
    draft_dir = tmp_path / "simple_name"
    draft_dir.mkdir()
    
    metadata = DraftMetadata.create_default(draft_dir)
    
    # Should default to the directory name itself when no timestamp format
    assert metadata.character_name == "unknown"


def test_metadata_update_modified(tmp_path):
    """Test updating modified timestamp."""
    draft_dir = tmp_path / "test_draft"
    draft_dir.mkdir()
    
    metadata = DraftMetadata(seed="Test")
    original_modified = metadata.modified
    
    # Wait a tiny bit and update
    import time
    time.sleep(0.01)
    
    metadata.update_modified()
    
    assert metadata.modified != original_modified


def test_metadata_roundtrip(tmp_path):
    """Test full save/load roundtrip."""
    draft_dir = tmp_path / "roundtrip_test"
    draft_dir.mkdir()
    
    # Create metadata with all fields
    original = DraftMetadata(
        seed="Complex character",
        mode="NSFW",
        model="openai/gpt-4",
        created="2026-02-05T10:00:00",
        modified="2026-02-05T11:00:00",
        tags=["fantasy", "knight", "hero"],
        genre="fantasy",
        notes="This is a test character with many tags",
        favorite=True,
        character_name="Sir Galahad"
    )
    
    # Save
    original.save(draft_dir)
    
    # Load
    loaded = DraftMetadata.load(draft_dir)
    
    # Verify all fields match
    assert loaded.seed == original.seed
    assert loaded.mode == original.mode
    assert loaded.model == original.model
    assert loaded.created == original.created
    assert loaded.modified == original.modified
    assert loaded.tags == original.tags
    assert loaded.genre == original.genre
    assert loaded.notes == original.notes
    assert loaded.favorite == original.favorite
    assert loaded.character_name == original.character_name


def test_metadata_json_format(tmp_path):
    """Test that saved JSON is properly formatted."""
    draft_dir = tmp_path / "json_format_test"
    draft_dir.mkdir()
    
    metadata = DraftMetadata(
        seed="Test",
        mode="SFW",
        tags=["tag1", "tag2"]
    )
    metadata.save(draft_dir)
    
    # Read and parse JSON
    metadata_file = draft_dir / ".metadata.json"
    with open(metadata_file) as f:
        data = json.load(f)
    
    # Verify it's valid and readable
    assert isinstance(data, dict)
    assert data["seed"] == "Test"
    assert data["mode"] == "SFW"
    assert data["tags"] == ["tag1", "tag2"]
