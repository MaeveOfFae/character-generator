"""Tests for bpui/export.py."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from bpui.features.export.export import export_character, export_with_preset


def _create_export_script(base_dir: Path, *, legacy: bool = False) -> Path:
    script = base_dir / "tools" / ("export_character.sh" if legacy else "generation/export_character.sh")
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/bin/bash\necho 'exported to output/test/'\nexit 0")
    script.chmod(0o755)
    return script


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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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
        _create_export_script(tmp_path)
        
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

        with patch("pathlib.Path.cwd", return_value=Path("/tmp/repo")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("subprocess.run", return_value=mock_result):
                    result = export_character(
                        "Test",
                        Path("/tmp/source")
                    )

        assert result["success"] is True

    def test_export_uses_legacy_script_path_as_fallback(self, tmp_path):
        """Test export still works if only the legacy script path exists."""
        _create_export_script(tmp_path, legacy=True)

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "✓ Character 'Test' exported to output/test/"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = export_character(
                "Test Character",
                source_dir,
                repo_root=tmp_path,
            )

        assert str(tmp_path / "tools" / "export_character.sh") == mock_run.call_args[0][0][0]
        assert result["success"] is True

    def test_raw_preset_exports_current_draft_layout(self, tmp_path):
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir(parents=True)
        (presets_dir / "raw.toml").write_text(
            """
[preset]
name = "Current Draft Layout"
format = "text"
description = "Current layout"

[[fields]]
asset = "system_prompt"
target = "system_prompt.txt"
            """.strip(),
            encoding="utf-8",
        )

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "system_prompt.md").write_text("System md", encoding="utf-8")
        (source_dir / "initial_message.md").write_text("Initial message", encoding="utf-8")

        result = export_with_preset(
            "Template Export",
            source_dir,
            "raw",
            repo_root=tmp_path,
        )

        assert result["success"] is True
        assert result["output_dir"] is not None
        assert (result["output_dir"] / "system_prompt.md").read_text(encoding="utf-8") == "System md"
        assert (result["output_dir"] / "initial_message.md").read_text(encoding="utf-8") == "Initial message"

    def test_raw_preset_removes_stale_files_from_existing_output_dir(self, tmp_path):
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir(parents=True)
        (presets_dir / "raw.toml").write_text(
            """
[preset]
name = "Current Draft Layout"
format = "text"
description = "Current layout"

[[fields]]
asset = "system_prompt"
target = "system_prompt.txt"
            """.strip(),
            encoding="utf-8",
        )

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "system_prompt.md").write_text("System md", encoding="utf-8")

        stale_output_dir = tmp_path / "output" / "template_export(unknown)"
        stale_output_dir.mkdir(parents=True)
        (stale_output_dir / "suno_prompt.txt").write_text("stale", encoding="utf-8")

        result = export_with_preset(
            "Template Export",
            source_dir,
            "raw",
            repo_root=tmp_path,
        )

        assert result["success"] is True
        assert not (result["output_dir"] / "suno_prompt.txt").exists()
