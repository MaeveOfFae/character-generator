"""Integration tests for end-to-end workflows."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from bpui.core.prompting import build_orchestrator_prompt, build_asset_prompt
from bpui.core.parse_blocks import parse_blueprint_output, extract_character_name
from bpui.utils.file_io.pack_io import create_draft_dir, list_drafts, load_draft
from bpui.utils.file_io.validate import validate_pack
from bpui.features.export.export import export_character


@pytest.fixture
def mock_complete_llm_output():
    """Mock complete 7-asset LLM output."""
    return """
```
system prompt content
```

```
post history content
```

```
name: Test Character
age: 25
occupation: Detective
heritage: Human

Core Concept:
A detective with psychic abilities.

Appearance:
Physical features: tall, dark hair
```

```
intro scene content
```

```markdown
# Test Character

Short description here.
```

```
[Control]
[Title: Test Portrait]
[Content: NSFW]
```

```
[Control]
[Title: Test Song]
[Genre: Rock]
```
"""


@pytest.fixture
def temp_repo_root(tmp_path):
    """Create a temporary repository root with required structure."""
    blueprints = tmp_path / "blueprints"
    blueprints.mkdir()
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    
    # Create minimal blueprints
    (blueprints / "rpbotgenerator.md").write_text("# RPBotGenerator\n\nOrchestrator blueprint.")
    (blueprints / "system_prompt.md").write_text("# System Prompt\n\nSystem prompt blueprint.")
    (blueprints / "post_history.md").write_text("# Post History\n\nPost history blueprint.")
    (blueprints / "character_sheet.md").write_text("# Character Sheet\n\nCharacter sheet blueprint.")
    (blueprints / "intro_scene.md").write_text("# Intro Scene\n\nIntro scene blueprint.")
    (blueprints / "intro_page.md").write_text("# Intro Page\n\nIntro page blueprint.")
    (blueprints / "a1111.md").write_text("# A1111\n\nA1111 blueprint.")
    (blueprints / "suno.md").write_text("# Suno\n\nSuno blueprint.")
    
    # Create export script
    export_script = tools / "export_character.sh"
    export_script.write_text("#!/bin/bash\necho 'Exported to output/test_character/'\n")
    export_script.chmod(0o755)
    
    return tmp_path


class TestCompileWorkflow:
    """Integration tests for full compile workflow."""
    
    @pytest.mark.asyncio
    async def test_full_compile_workflow(self, mock_complete_llm_output, temp_repo_root):
        """Test complete workflow: seed → prompt → LLM → parse → save."""
        seed = "Noir detective with psychic abilities"
        mode = "NSFW"
        
        # Step 1: Build orchestrator prompt
        blueprint, prompt = build_orchestrator_prompt(seed, mode=mode, repo_root=temp_repo_root)
        assert seed in prompt
        assert mode in prompt
        
        # Step 2: Mock LLM call
        mock_engine = AsyncMock()
        mock_engine.generate.return_value = mock_complete_llm_output
        
        llm_output = await mock_engine.generate(prompt)
        assert "Test Character" in llm_output
        
        # Step 3: Parse output
        assets = parse_blueprint_output(llm_output)
        assert len(assets) == 7
        assert "system_prompt" in assets
        assert "character_sheet" in assets
        
        # Step 4: Extract character name
        char_name = extract_character_name(assets["character_sheet"])
        assert char_name == "test_character"
        
        # Step 5: Save draft
        draft_dir = create_draft_dir(
            assets=assets,
            character_name=char_name,
            drafts_root=temp_repo_root / "drafts"
        )
        assert draft_dir.exists()
        assert (draft_dir / "system_prompt.txt").exists()
        assert (draft_dir / "character_sheet.txt").exists()
        
        # Step 6: Verify draft can be loaded
        loaded = load_draft(draft_dir)
        assert loaded["system_prompt"] == assets["system_prompt"]
        assert loaded["character_sheet"] == assets["character_sheet"]
    
    @pytest.mark.asyncio
    async def test_compile_with_adjustment_note(self, temp_repo_root):
        """Test workflow handles adjustment note correctly."""
        llm_output = """
```
Adjustment Note: Seed augmented for clarity.
```

```
system prompt
```

```
post history
```

```
name: Adjusted Character
age: 30
```

```
intro scene
```

```markdown
# Adjusted Character
```

```
[Control]
```

```
[Control]
```
"""
        # Parse should extract 7 assets, skipping adjustment note
        assets = parse_blueprint_output(llm_output)
        assert len(assets) == 7
        assert "system_prompt" in assets
        assert assets["system_prompt"] == "system prompt"
    
    @pytest.mark.asyncio
    async def test_compile_workflow_with_streaming(self, temp_repo_root):
        """Test workflow with streaming LLM output."""
        chunks = [
            "```\n",
            "system prompt content\n",
            "```\n\n",
            "```\n",
            "post history\n",
            "```\n"
        ]
        
        mock_engine = AsyncMock()
        
        async def mock_stream(prompt):
            for chunk in chunks:
                yield chunk
        
        mock_engine.generate_stream = mock_stream
        
        # Collect streamed output
        full_output = ""
        async for chunk in mock_engine.generate_stream("test prompt"):
            full_output += chunk
        
        assert "system prompt content" in full_output
        assert "post history" in full_output


class TestValidationWorkflow:
    """Integration tests for validation workflow."""
    
    @pytest.mark.skip(reason="Mock patching issue - validation tested in unit tests")
    def test_validation_workflow(self, temp_repo_root):
        """Test complete validation workflow: create pack → validate → report."""
        # Step 1: Create a draft with validation issues
        assets = {
            "system_prompt": "Valid system prompt",
            "post_history": "Valid post history",
            "character_sheet": "name: Test\nage: {AGE}\n",  # placeholder issue
            "intro_scene": "Valid scene",
            "intro_page": "# Test\n\n{PLACEHOLDER}",  # placeholder issue
            "a1111": "[Control]\n[Content: SFW]",
            "suno": "[Control]\n[Title: Song]"
        }
        
        draft_dir = create_draft_dir(
            assets=assets,
            character_name="test_validation",
            drafts_root=temp_repo_root / "drafts"
        )
        
        # Step 2: Run validation (mock the validator script)
        with patch("bpui.utils.file_io.validate.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = "Found placeholder: {AGE}\\nFound placeholder: {PLACEHOLDER}\\n"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = validate_pack(draft_dir, repo_root=temp_repo_root)
            
            assert result["success"] is False
            assert result["exit_code"] == 1
            assert "{AGE}" in result["output"] or "{PLACEHOLDER}" in result["output"]
    
    @pytest.mark.skip(reason="Mock patching issue - validation tested in unit tests")
    def test_validation_passes_clean_pack(self, temp_repo_root):
        """Test validation passes for clean pack."""
        # Create a clean draft
        assets = {
            "system_prompt": "Valid system prompt",
            "post_history": "Valid post history",
            "character_sheet": "name: Clean Character\nage: 25\n",
            "intro_scene": "Valid scene",
            "intro_page": "# Clean Character\n\nDescription",
            "a1111": "[Control]\n[Content: NSFW]",
            "suno": "[Control]\n[Title: Song]"
        }
        
        draft_dir = create_draft_dir(
            assets=assets,
            character_name="clean_character",
            drafts_root=temp_repo_root / "drafts"
        )
        
        # Mock validation passing
        with patch("bpui.utils.file_io.validate.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="✓ All validations passed\n"
            )
            
            result = validate_pack(draft_dir, repo_root=temp_repo_root)
            
            assert result["success"] is True


class TestExportWorkflow:
    """Integration tests for export workflow."""
    
    def test_export_workflow(self, temp_repo_root):
        """Test complete export workflow: draft → export → verify output."""
        # Step 1: Create a draft
        assets = {
            "system_prompt": "Export test system",
            "post_history": "Export test post",
            "character_sheet": "name: Export Character\nage: 30\n",
            "intro_scene": "Export scene",
            "intro_page": "# Export Character",
            "a1111": "[Control]",
            "suno": "[Control]"
        }
        
        draft_dir = create_draft_dir(
            assets=assets,
            character_name="export_character",
            drafts_root=temp_repo_root / "drafts"
        )
        
        # Step 2: Export
        with patch("bpui.features.export.export.subprocess.run") as mock_run:
            output_path = temp_repo_root / "output" / "export_character(test_model)"
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=f"✓ Character 'Export Character' exported to {output_path}/\n"
            )
            
            result = export_character(
                character_name="Export Character",
                source_dir=draft_dir,
                model="test_model",
                repo_root=temp_repo_root
            )
            
            assert result["success"] is True
            assert str(output_path) in result["output"]
    
    def test_export_roundtrip(self, temp_repo_root):
        """Test draft → export → load exported pack."""
        # Create and export a draft
        assets = {
            "system_prompt": "Roundtrip system",
            "post_history": "Roundtrip post",
            "character_sheet": "name: Roundtrip Character\nage: 28\n",
            "intro_scene": "Roundtrip scene",
            "intro_page": "# Roundtrip Character",
            "a1111": "[Control]\n[Content: NSFW]",
            "suno": "[Control]\n[Title: Theme]"
        }
        
        draft_dir = create_draft_dir(
            assets=assets,
            character_name="roundtrip_character",
            drafts_root=temp_repo_root / "drafts"
        )
        
        # Mock export that actually copies files
        output_dir = temp_repo_root / "output" / "roundtrip_character(model)"
        output_dir.mkdir(parents=True)
        
        with patch("bpui.features.export.export.subprocess.run") as mock_run:
            # Simulate export by copying files
            for filename in ["system_prompt.txt", "post_history.txt", "character_sheet.txt",
                           "intro_scene.txt", "intro_page.md", "a1111_prompt.txt", "suno_prompt.txt"]:
                src = draft_dir / filename
                dst = output_dir / filename
                if src.exists():
                    shutil.copy(src, dst)
            
            mock_run.return_value = MagicMock(returncode=0, stdout=f"Exported to {output_dir}/")
            
            result = export_character(
                character_name="Roundtrip Character",
                source_dir=draft_dir,
                model="model",
                repo_root=temp_repo_root
            )
            
            assert result["success"] is True
        
        # Load exported pack
        loaded = load_draft(output_dir)
        assert loaded["system_prompt"] == assets["system_prompt"]
        assert loaded["character_sheet"] == assets["character_sheet"]


class TestMultiAssetGeneration:
    """Integration tests for multi-asset generation scenarios."""
    
    @pytest.mark.asyncio
    async def test_hierarchical_asset_generation(self, temp_repo_root):
        """Test generating assets in hierarchy order."""
        seed = "Test character"
        mode = "NSFW"
        
        # Simulate generating assets in order
        prior_assets = {}
        asset_order = ["system_prompt", "post_history", "character_sheet", 
                      "intro_scene", "intro_page", "a1111", "suno"]
        
        for asset_name in asset_order:
            # Build prompt with prior assets
            blueprint, prompt = build_asset_prompt(
                seed=seed,
                asset_name=asset_name,
                mode=mode,
                prior_assets=prior_assets,
                repo_root=temp_repo_root
            )
            
            assert seed in prompt
            
            # Verify prior assets are referenced in prompt
            for prior_name, prior_content in prior_assets.items():
                if prior_content:  # Only check non-empty assets
                    # Just verify prompt was built successfully
                    assert prompt is not None
            
            # Mock generation
            prior_assets[asset_name] = f"Generated {asset_name} content"
        
        # Verify all assets generated
        assert len(prior_assets) == 7
    
    def test_draft_management_workflow(self, temp_repo_root):
        """Test full draft lifecycle: create → list → load → delete."""
        drafts_root = temp_repo_root / "drafts"
        
        # Create multiple drafts
        for i in range(3):
            assets = {
                "system_prompt": f"System {i}",
                "post_history": f"Post {i}",
                "character_sheet": f"name: Character {i}\nage: {20+i}\n",
                "intro_scene": f"Scene {i}",
                "intro_page": f"# Character {i}",
                "a1111": "[Control]",
                "suno": "[Control]"
            }
            create_draft_dir(
                assets=assets,
                character_name=f"character_{i}",
                drafts_root=drafts_root
            )
        
        # List drafts
        drafts = list_drafts(drafts_root)
        assert len(drafts) >= 3
        
        # Load first draft
        first_draft = drafts[0]
        loaded = load_draft(first_draft)
        assert "system_prompt" in loaded
        
        # Delete draft (would be tested but we keep files for other tests)
        # delete_draft(first_draft["path"])


class TestErrorRecovery:
    """Integration tests for error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_incomplete_llm_output_handling(self):
        """Test handling of incomplete LLM output."""
        from bpui.core.parse_blocks import ParseError
        
        incomplete_output = """
```
system prompt
```

```
post history
```
"""
        # Should raise ParseError for missing assets
        with pytest.raises(ParseError, match="Expected 7 asset blocks"):
            parse_blueprint_output(incomplete_output)
    
    def test_missing_character_name_recovery(self):
        """Test fallback when character name cannot be extracted."""
        from bpui.core.parse_blocks import ParseError
        
        sheet_no_name = "age: 25\noccupation: Detective"
        
        # extract_character_name returns None if no name found (not raise)
        name = extract_character_name(sheet_no_name)
        assert name is None or name == ""
    
    def test_validation_on_corrupted_pack(self, temp_repo_root):
        """Test validation handles corrupted pack gracefully."""
        # Create pack with missing files
        pack_dir = temp_repo_root / "drafts" / "corrupted_pack"
        pack_dir.mkdir(parents=True)
        (pack_dir / "system_prompt.txt").write_text("Only file")
        
        # Validation should handle missing files
        with patch("bpui.utils.file_io.validate.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Error: Missing required files\n"
            )
            
            result = validate_pack(pack_dir, repo_root=temp_repo_root)
            assert result["success"] is False
