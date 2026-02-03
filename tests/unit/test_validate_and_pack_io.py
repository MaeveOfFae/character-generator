"""Tests for bpui/validate.py and bpui/pack_io.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from bpui.validate import validate_pack
from bpui.pack_io import (
    create_draft_dir,
    list_drafts,
    load_draft,
    delete_draft,
)


class TestValidatePack:
    """Tests for validate_pack function."""
    
    def test_validate_missing_validator(self, tmp_path):
        """Test validation when validator script is missing."""
        result = validate_pack(tmp_path, repo_root=tmp_path)
        
        assert result["success"] is False
        assert "Validator not found" in result["errors"]
        assert result["exit_code"] == 1
    
    def test_validate_valid_pack(self):
        """Test validation of a valid pack."""
        repo_root = Path(__file__).parent.parent.parent
        pack_dir = repo_root / "fixtures" / "sample_pack"
        
        if not pack_dir.exists():
            pytest.skip("Sample pack not found")
        
        result = validate_pack(pack_dir, repo_root)
        
        assert "output" in result
        assert "errors" in result
        assert "exit_code" in result
        assert "success" in result
    
    def test_validate_missing_pack(self):
        """Test validation of non-existent pack."""
        repo_root = Path(__file__).parent.parent.parent
        pack_dir = Path("/nonexistent/pack/dir")
        
        result = validate_pack(pack_dir, repo_root)
        
        # Should fail because directory doesn't exist
        assert result["success"] is False
    
    def test_validate_with_default_repo_root(self, tmp_path, monkeypatch):
        """Test validation uses cwd when repo_root is None."""
        monkeypatch.chdir(tmp_path)
        
        # Create fake validator
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        validator = tools_dir / "validate_pack.py"
        validator.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)")
        
        pack_dir = tmp_path / "test_pack"
        pack_dir.mkdir()
        
        with patch("bpui.validate.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Valid",
                stderr=""
            )
            result = validate_pack(pack_dir)  # No repo_root argument
            
            assert result["success"] is True
            mock_run.assert_called_once()
    
    def test_validate_timeout(self, tmp_path):
        """Test validation handles timeout."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        validator = tools_dir / "validate_pack.py"
        validator.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)")
        
        pack_dir = tmp_path / "test_pack"
        pack_dir.mkdir()
        
        with patch("bpui.validate.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("python3", 30)
            
            result = validate_pack(pack_dir, repo_root=tmp_path)
            
            assert result["success"] is False
            assert "timed out" in result["errors"]
            assert result["exit_code"] == 124
    
    def test_validate_subprocess_exception(self, tmp_path):
        """Test validation handles subprocess exceptions."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        validator = tools_dir / "validate_pack.py"
        validator.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)")
        
        pack_dir = tmp_path / "test_pack"
        pack_dir.mkdir()
        
        with patch("bpui.validate.subprocess.run") as mock_run:
            mock_run.side_effect = OSError("Permission denied")
            
            result = validate_pack(pack_dir, repo_root=tmp_path)
            
            assert result["success"] is False
            assert "Permission denied" in result["errors"]
            assert result["exit_code"] == 1


class TestCreateDraftDir:
    """Tests for create_draft_dir function."""
    
    def test_create_basic_draft(self, tmp_path):
        """Test creating a basic draft directory."""
        assets = {
            "system_prompt": "You are a detective.",
            "post_history": "Jake is investigating a case.",
            "character_sheet": "name: Jake\nage: 35",
        }
        
        draft_dir = create_draft_dir(assets, "jake", tmp_path)
        
        assert draft_dir.exists()
        assert draft_dir.parent == tmp_path
        assert "jake" in draft_dir.name
        assert (draft_dir / "system_prompt.txt").exists()
        assert (draft_dir / "post_history.txt").exists()
        assert (draft_dir / "character_sheet.txt").exists()
    
    def test_create_draft_all_assets(self, tmp_path):
        """Test creating draft with all assets."""
        assets = {
            "system_prompt": "system",
            "post_history": "post",
            "character_sheet": "sheet",
            "intro_scene": "scene",
            "intro_page": "page",
            "a1111": "a1111",
            "suno": "suno",
        }
        
        draft_dir = create_draft_dir(assets, "test_char", tmp_path)
        
        assert (draft_dir / "system_prompt.txt").read_text() == "system"
        assert (draft_dir / "post_history.txt").read_text() == "post"
        assert (draft_dir / "character_sheet.txt").read_text() == "sheet"
        assert (draft_dir / "intro_scene.txt").read_text() == "scene"
        assert (draft_dir / "intro_page.md").read_text() == "page"
        assert (draft_dir / "a1111_prompt.txt").read_text() == "a1111"
        assert (draft_dir / "suno_prompt.txt").read_text() == "suno"
    
    def test_create_draft_timestamped(self, tmp_path):
        """Test that draft directories are timestamped."""
        assets = {"system_prompt": "test"}
        
        draft1 = create_draft_dir(assets, "char1", tmp_path)
        draft2 = create_draft_dir(assets, "char2", tmp_path)
        
        # Should have different names (timestamps)
        assert draft1.name != draft2.name
        assert "char1" in draft1.name
        assert "char2" in draft2.name
    
    def test_create_draft_creates_parent(self, tmp_path):
        """Test that drafts root is created if missing."""
        drafts_root = tmp_path / "new_drafts"
        assets = {"system_prompt": "test"}
        
        assert not drafts_root.exists()
        
        draft_dir = create_draft_dir(assets, "test", drafts_root)
        
        assert drafts_root.exists()
        assert draft_dir.exists()


class TestListDrafts:
    """Tests for list_drafts function."""
    
    def test_list_empty_directory(self, tmp_path):
        """Test listing when no drafts exist."""
        drafts = list_drafts(tmp_path)
        assert drafts == []
    
    def test_list_multiple_drafts(self, tmp_path):
        """Test listing multiple drafts."""
        assets = {"system_prompt": "test"}
        
        draft1 = create_draft_dir(assets, "char1", tmp_path)
        draft2 = create_draft_dir(assets, "char2", tmp_path)
        draft3 = create_draft_dir(assets, "char3", tmp_path)
        
        drafts = list_drafts(tmp_path)
        
        assert len(drafts) == 3
        assert draft1 in drafts
        assert draft2 in drafts
        assert draft3 in drafts
    
    def test_list_sorted_newest_first(self, tmp_path):
        """Test that drafts are sorted newest first."""
        assets = {"system_prompt": "test"}
        
        draft1 = create_draft_dir(assets, "old", tmp_path)
        draft2 = create_draft_dir(assets, "new", tmp_path)
        
        drafts = list_drafts(tmp_path)
        
        # Newer draft should come first
        assert drafts[0].name > drafts[1].name
    
    def test_list_nonexistent_directory(self, tmp_path):
        """Test listing when drafts directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        drafts = list_drafts(nonexistent)
        
        assert drafts == []
    
    def test_list_ignores_files(self, tmp_path):
        """Test that files are ignored, only directories listed."""
        # Create a file in drafts root
        (tmp_path / "not_a_draft.txt").write_text("test")
        
        # Create a draft directory
        assets = {"system_prompt": "test"}
        draft = create_draft_dir(assets, "char", tmp_path)
        
        drafts = list_drafts(tmp_path)
        
        assert len(drafts) == 1
        assert drafts[0] == draft


class TestLoadDraft:
    """Tests for load_draft function."""
    
    def test_load_complete_draft(self, tmp_path):
        """Test loading a complete draft."""
        original_assets = {
            "system_prompt": "You are Jake.",
            "post_history": "Jake is a detective.",
            "character_sheet": "name: Jake",
            "intro_scene": "Jake enters the room.",
        }
        
        draft_dir = create_draft_dir(original_assets, "jake", tmp_path)
        loaded_assets = load_draft(draft_dir)
        
        assert loaded_assets["system_prompt"] == "You are Jake."
        assert loaded_assets["post_history"] == "Jake is a detective."
        assert loaded_assets["character_sheet"] == "name: Jake"
        assert loaded_assets["intro_scene"] == "Jake enters the room."
    
    def test_load_partial_draft(self, tmp_path):
        """Test loading a draft with missing assets."""
        assets = {
            "system_prompt": "test",
        }
        
        draft_dir = create_draft_dir(assets, "partial", tmp_path)
        loaded_assets = load_draft(draft_dir)
        
        assert "system_prompt" in loaded_assets
        assert "post_history" not in loaded_assets
        assert "character_sheet" not in loaded_assets
    
    def test_load_empty_draft(self, tmp_path):
        """Test loading an empty draft directory."""
        draft_dir = tmp_path / "empty_draft"
        draft_dir.mkdir()
        
        loaded_assets = load_draft(draft_dir)
        
        assert loaded_assets == {}
    
    def test_load_all_assets(self, tmp_path):
        """Test loading all seven assets."""
        all_assets = {
            "system_prompt": "sys",
            "post_history": "post",
            "character_sheet": "sheet",
            "intro_scene": "scene",
            "intro_page": "page",
            "a1111": "a1111",
            "suno": "suno",
        }
        
        draft_dir = create_draft_dir(all_assets, "full", tmp_path)
        loaded_assets = load_draft(draft_dir)
        
        assert len(loaded_assets) == 7
        assert loaded_assets == all_assets


class TestDeleteDraft:
    """Tests for delete_draft function."""
    
    def test_delete_existing_draft(self, tmp_path):
        """Test deleting an existing draft."""
        assets = {"system_prompt": "test"}
        draft_dir = create_draft_dir(assets, "to_delete", tmp_path)
        
        assert draft_dir.exists()
        
        delete_draft(draft_dir)
        
        assert not draft_dir.exists()
    
    def test_delete_nonexistent_draft(self, tmp_path):
        """Test deleting a non-existent draft (should not error)."""
        nonexistent = tmp_path / "nonexistent_draft"
        
        # Should not raise an exception
        delete_draft(nonexistent)
    
    def test_delete_removes_all_files(self, tmp_path):
        """Test that deletion removes all files."""
        assets = {
            "system_prompt": "sys",
            "post_history": "post",
            "character_sheet": "sheet",
        }
        draft_dir = create_draft_dir(assets, "full_delete", tmp_path)
        
        # Verify files exist
        assert (draft_dir / "system_prompt.txt").exists()
        assert (draft_dir / "post_history.txt").exists()
        
        delete_draft(draft_dir)
        
        # Directory and all files should be gone
        assert not draft_dir.exists()
        assert not (draft_dir / "system_prompt.txt").exists()


class TestRoundTripIO:
    """Integration tests for create/load/delete cycle."""
    
    def test_create_load_roundtrip(self, tmp_path):
        """Test create → load roundtrip."""
        original = {
            "system_prompt": "original system",
            "character_sheet": "original sheet",
        }
        
        draft_dir = create_draft_dir(original, "roundtrip", tmp_path)
        loaded = load_draft(draft_dir)
        
        assert loaded == original
    
    def test_create_list_load_delete(self, tmp_path):
        """Test full lifecycle: create → list → load → delete."""
        assets = {"system_prompt": "lifecycle test"}
        
        # Create
        draft_dir = create_draft_dir(assets, "lifecycle", tmp_path)
        
        # List
        drafts = list_drafts(tmp_path)
        assert len(drafts) == 1
        assert drafts[0] == draft_dir
        
        # Load
        loaded = load_draft(draft_dir)
        assert loaded["system_prompt"] == "lifecycle test"
        
        # Delete
        delete_draft(draft_dir)
        drafts = list_drafts(tmp_path)
        assert len(drafts) == 0
