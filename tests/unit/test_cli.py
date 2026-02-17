"""Tests for bpui/cli.py."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import sys

# Check if textual is available
try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


class TestMainArgumentParsing:
    """Tests for CLI argument parsing."""
    
    def test_no_args_defaults_to_gui(self):
        """Test that no arguments defaults to GUI."""
        with patch("sys.argv", ["bpui"]):
            with patch("bpui.core.cli.run_gui") as mock_gui:
                from bpui.core.cli import main
                main()
                mock_gui.assert_called_once()
    
    def test_tui_command(self):
        """Test explicit tui command."""
        with patch("sys.argv", ["bpui", "tui"]):
            with patch("bpui.cli.run_tui") as mock_tui:
                from bpui.core.cli import main
                main()
                mock_tui.assert_called_once()
    
    def test_compile_command_requires_seed(self):
        """Test that compile requires --seed."""
        with patch("sys.argv", ["bpui", "compile"]):
            with pytest.raises(SystemExit):
                from bpui.core.cli import main
                main()
    
    def test_seedgen_command_requires_input(self):
        """Test that seed-gen requires --input."""
        with patch("sys.argv", ["bpui", "seed-gen"]):
            with pytest.raises(SystemExit):
                from bpui.core.cli import main
                main()
    
    def test_validate_command_requires_directory(self):
        """Test that validate requires directory."""
        with patch("sys.argv", ["bpui", "validate"]):
            with pytest.raises(SystemExit):
                from bpui.core.cli import main
                main()
    
    def test_export_command_requires_args(self):
        """Test that export requires character_name and source_dir."""
        with patch("sys.argv", ["bpui", "export"]):
            with pytest.raises(SystemExit):
                from bpui.core.cli import main
                main()


class TestRunTui:
    """Tests for run_tui function."""
    
    @pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual not installed")
    def test_run_tui_launches_app(self):
        """Test that run_tui launches BlueprintUI."""
        with patch("bpui.tui.app.BlueprintUI") as mock_ui:
            mock_app = MagicMock()
            mock_ui.return_value = mock_app
            
            from bpui.cli import run_tui
            run_tui()
            
            mock_ui.assert_called_once()
            mock_app.run.assert_called_once()


class TestRunCompile:
    """Tests for run_compile function."""
    
    @pytest.mark.asyncio
    async def test_compile_basic(self):
        """Test basic compilation."""
        from argparse import Namespace
        
        args = Namespace(
            seed="A detective",
            mode=None,
            out=None,
            model=None
        )
        
        # Mock Config
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "litellm"
        
        # Mock Engine
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Asset content")
        
        # Mock functions at the point they're imported in run_compile
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.litellm_engine.LiteLLMEngine", return_value=mock_engine):
                with patch("bpui.prompting.build_asset_prompt", return_value=("sys", "user")):
                    with patch("bpui.parse_blocks.extract_single_asset", return_value="content"):
                        with patch("bpui.parse_blocks.extract_character_name", return_value="test_char"):
                            with patch("bpui.pack_io.create_draft_dir", return_value=Path("/tmp/test")) as mock_create:
                                with patch("builtins.print"):
                                    from bpui.cli import run_compile
                                    await run_compile(args)
                                    
                                    mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compile_with_mode(self):
        """Test compilation with content mode."""
        from argparse import Namespace
        
        args = Namespace(
            seed="A detective",
            mode="NSFW",
            out=None,
            model=None
        )
        
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "litellm"
        
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Asset content")
        
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.litellm_engine.LiteLLMEngine", return_value=mock_engine):
                with patch("bpui.prompting.build_asset_prompt", return_value=("sys", "user")) as mock_build:
                    with patch("bpui.parse_blocks.extract_single_asset", return_value="content"):
                        with patch("bpui.parse_blocks.extract_character_name", return_value="char"):
                            with patch("bpui.pack_io.create_draft_dir", return_value=Path("/tmp/test")):
                                with patch("builtins.print"):
                                    from bpui.cli import run_compile
                                    await run_compile(args)
                                    
                                    # Verify mode was passed
                                    calls = mock_build.call_args_list
                                    assert any("NSFW" in str(call) for call in calls)
    
    @pytest.mark.asyncio
    async def test_compile_with_custom_output(self, tmp_path):
        """Test compilation with custom output directory."""
        from argparse import Namespace
        
        output_dir = tmp_path / "output"
        
        args = Namespace(
            seed="A detective",
            mode=None,
            out=str(output_dir),
            model=None
        )
        
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "litellm"
        
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Asset content")
        
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.litellm_engine.LiteLLMEngine", return_value=mock_engine):
                with patch("bpui.prompting.build_asset_prompt", return_value=("sys", "user")):
                    with patch("bpui.parse_blocks.extract_single_asset", return_value="content"):
                        with patch("bpui.parse_blocks.extract_character_name", return_value="char"):
                            with patch("builtins.print"):
                                from bpui.cli import run_compile
                                await run_compile(args)
                                
                                # Verify output directory was created
                                assert output_dir.exists()
    
    @pytest.mark.asyncio
    async def test_compile_with_openai_compat_engine(self):
        """Test compilation with OpenAI-compatible engine."""
        from argparse import Namespace
        
        args = Namespace(
            seed="A detective",
            mode=None,
            out=None,
            model=None
        )
        
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "openai_compatible"
        mock_config.base_url = "http://localhost:8000"
        
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Asset content")
        
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.openai_compat_engine.OpenAICompatEngine", return_value=mock_engine) as mock_openai:
                with patch("bpui.prompting.build_asset_prompt", return_value=("sys", "user")):
                    with patch("bpui.parse_blocks.extract_single_asset", return_value="content"):
                        with patch("bpui.parse_blocks.extract_character_name", return_value="char"):
                            with patch("bpui.pack_io.create_draft_dir", return_value=Path("/tmp/test")):
                                with patch("builtins.print"):
                                    from bpui.cli import run_compile
                                    await run_compile(args)
                                    
                                    mock_openai.assert_called_once()


class TestRunSeedgen:
    """Tests for run_seedgen function."""
    
    @pytest.mark.asyncio
    async def test_seedgen_basic(self, tmp_path):
        """Test basic seed generation."""
        from argparse import Namespace
        
        # Create input file
        input_file = tmp_path / "genres.txt"
        input_file.write_text("Cyberpunk\nNoir")
        
        args = Namespace(
            input=str(input_file),
            out=None
        )
        
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "litellm"
        
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Seed 1\nSeed 2\nSeed 3")
        
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.litellm_engine.LiteLLMEngine", return_value=mock_engine):
                with patch("bpui.prompting.build_seedgen_prompt", return_value=("sys", "user")):
                    with patch("builtins.print"):
                        from bpui.core.cli import run_seedgen
                        await run_seedgen(args)
    
    @pytest.mark.asyncio
    async def test_seedgen_with_output(self, tmp_path):
        """Test seed generation with output file."""
        from argparse import Namespace
        
        input_file = tmp_path / "genres.txt"
        input_file.write_text("Cyberpunk")
        
        output_file = tmp_path / "seeds.txt"
        
        args = Namespace(
            input=str(input_file),
            out=str(output_file)
        )
        
        mock_config = MagicMock()
        mock_config.model = "test/model"
        mock_config.api_key = "sk-test"
        mock_config.temperature = 0.7
        mock_config.max_tokens = 4096
        mock_config.engine = "litellm"
        
        mock_engine = MagicMock()
        mock_engine.generate = AsyncMock(return_value="Seed 1\nSeed 2")
        
        with patch("bpui.core.config.Config", return_value=mock_config):
            with patch("bpui.llm.litellm_engine.LiteLLMEngine", return_value=mock_engine):
                with patch("bpui.prompting.build_seedgen_prompt", return_value=("sys", "user")):
                    with patch("builtins.print"):
                        from bpui.core.cli import run_seedgen
                        await run_seedgen(args)
                        
                        assert output_file.exists()
                        content = output_file.read_text()
                        assert "Seed 1" in content
    
    @pytest.mark.asyncio
    async def test_seedgen_missing_input(self):
        """Test seed generation with missing input file."""
        from argparse import Namespace
        
        args = Namespace(
            input="/nonexistent/file.txt",
            out=None
        )
        
        with patch("builtins.print"):
            with pytest.raises(SystemExit) as exc:
                from bpui.core.cli import run_seedgen
                await run_seedgen(args)
            assert exc.value.code == 1


class TestRunValidate:
    """Tests for run_validate function."""
    
    def test_validate_existing_pack(self, tmp_path):
        """Test validating an existing pack."""
        from argparse import Namespace
        
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()
        
        args = Namespace(directory=str(pack_dir))
        
        mock_result = {
            "success": True,
            "output": "Validation passed",
            "errors": "",
            "exit_code": 0
        }
        
        with patch("bpui.utils.file_io.validate.validate_pack", return_value=mock_result):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc:
                    from bpui.core.cli import run_validate
                    run_validate(args)
                assert exc.value.code == 0
    
    def test_validate_missing_pack(self):
        """Test validating non-existent pack."""
        from argparse import Namespace
        
        args = Namespace(directory="/nonexistent/pack")
        
        with patch("builtins.print"):
            with pytest.raises(SystemExit) as exc:
                from bpui.core.cli import run_validate
                run_validate(args)
            assert exc.value.code == 1
    
    def test_validate_with_errors(self, tmp_path):
        """Test validation with errors."""
        from argparse import Namespace
        
        pack_dir = tmp_path / "pack"
        pack_dir.mkdir()
        
        args = Namespace(directory=str(pack_dir))
        
        mock_result = {
            "success": False,
            "output": "Validation failed",
            "errors": "Missing files",
            "exit_code": 1
        }
        
        with patch("bpui.utils.file_io.validate.validate_pack", return_value=mock_result):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc:
                    from bpui.core.cli import run_validate
                    run_validate(args)
                assert exc.value.code == 1


class TestRunExport:
    """Tests for run_export function."""
    
    def test_export_success(self, tmp_path):
        """Test successful export."""
        from argparse import Namespace
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        args = Namespace(
            character_name="Test Character",
            source_dir=str(source_dir),
            model="test_model"
        )
        
        mock_result = {
            "success": True,
            "output": "Export successful",
            "errors": "",
            "exit_code": 0
        }
        
        with patch("bpui.features.export.export.export_character", return_value=mock_result):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc:
                    from bpui.core.cli import run_export
                    run_export(args)
                assert exc.value.code == 0
    
    def test_export_missing_source(self):
        """Test export with missing source directory."""
        from argparse import Namespace
        
        args = Namespace(
            character_name="Test",
            source_dir="/nonexistent/source",
            model=None
        )
        
        with patch("builtins.print"):
            with pytest.raises(SystemExit) as exc:
                from bpui.core.cli import run_export
                run_export(args)
            assert exc.value.code == 1
    
    def test_export_with_errors(self, tmp_path):
        """Test export with errors."""
        from argparse import Namespace
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        args = Namespace(
            character_name="Test",
            source_dir=str(source_dir),
            model=None
        )
        
        mock_result = {
            "success": False,
            "output": "Export failed",
            "errors": "Missing files",
            "exit_code": 1
        }
        
        with patch("bpui.features.export.export.export_character", return_value=mock_result):
            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc:
                    from bpui.core.cli import run_export
                    run_export(args)
                assert exc.value.code == 1
