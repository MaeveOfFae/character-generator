"""Tests for bpui/export.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from bpui.features.export.export import export_character


class TestExportCharacter:
    """Tests for export_character function."""
    
    def test_export_missing_script(self, tmp_path):
        """Test export when script is missing."""
        result = export_character(
            "Test Character",
            tmp_path / "source",
            repo_root=tmp_path
        )
        
        assert result["success"] is False
        assert "Export script not found" in result["errors"]
        assert result["exit_code"] == 1
        assert result["output_dir"] is None
    
    def test_export_success(self, tmp_path):
        """Test successful export."""
        # Create mock script
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.write_text("#!/bin/bash\necho 'exported to output/test/'\nexit 0")
        script.chmod(0o755)
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "✓ Character 'Test' exported to output/test/"
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            result = export_character(
                "Test Character",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "exported to" in result["output"]
    
    def test_export_with_model(self, tmp_path):
        """Test export with model parameter."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "exported to output/test(gpt4)/"
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = export_character(
                "Test",
                source_dir,
                model="gpt4",
                repo_root=tmp_path
            )
            
            # Verify model was passed
            call_args = mock_run.call_args[0][0]
            assert "gpt4" in call_args
        
        assert result["success"] is True
    
    def test_export_timeout(self, tmp_path):
        """Test export timeout."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = export_character(
                "Test",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["success"] is False
        assert "timed out" in result["errors"]
        assert result["exit_code"] == 124
        assert result["output_dir"] is None
    
    def test_export_error(self, tmp_path):
        """Test export with error."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Missing files"
        
        with patch("subprocess.run", return_value=mock_result):
            result = export_character(
                "Test",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "Missing files" in result["errors"]
    
    def test_export_exception(self, tmp_path):
        """Test export with generic exception."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        with patch("subprocess.run", side_effect=Exception("Unexpected error")):
            result = export_character(
                "Test",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["success"] is False
        assert "Unexpected error" in result["errors"]
        assert result["output_dir"] is None
    
    def test_export_parses_output_directory(self, tmp_path):
        """Test that output directory is parsed from stdout."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "✓ Character exported to output/test_char(model)/"
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            result = export_character(
                "Test",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["output_dir"] is not None
        assert "output/test_char(model)" in str(result["output_dir"])
    
    def test_export_no_output_directory_on_failure(self, tmp_path):
        """Test that output_dir is None on failure."""
        script = tmp_path / "tools" / "export_character.sh"
        script.parent.mkdir(parents=True)
        script.touch()
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Failed"
        
        with patch("subprocess.run", return_value=mock_result):
            result = export_character(
                "Test",
                source_dir,
                repo_root=tmp_path
            )
        
        assert result["output_dir"] is None
    
    def test_export_with_default_repo_root(self):
        """Test export with default repo root (cwd)."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        
        # Mock Path.cwd() and script existence
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_repo = MagicMock()
            mock_script = MagicMock()
            mock_script.exists.return_value = True
            mock_repo.__truediv__.return_value = mock_script
            mock_cwd.return_value = mock_repo
            
            with patch("subprocess.run", return_value=mock_result):
                result = export_character(
                    "Test",
                    Path("/tmp/source")
                )
            
            assert result["success"] is True
