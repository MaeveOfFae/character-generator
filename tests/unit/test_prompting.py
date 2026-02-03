"""Tests for bpui/prompting.py."""

import pytest
from pathlib import Path
from bpui.prompting import (
    load_blueprint,
    build_orchestrator_prompt,
    build_asset_prompt,
    build_seedgen_prompt,
)


class TestLoadBlueprint:
    """Tests for load_blueprint function."""
    
    def test_load_existing_blueprint(self):
        """Test loading an existing blueprint."""
        # Use actual repo root
        repo_root = Path(__file__).parent.parent.parent
        content = load_blueprint("rpbotgenerator", repo_root)
        
        assert "RPBotGenerator Orchestrator" in content
        assert "SEED" in content
    
    def test_load_nonexistent_blueprint(self, tmp_path):
        """Test loading a blueprint that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_blueprint("nonexistent", tmp_path)
    
    def test_load_system_prompt_blueprint(self):
        """Test loading system_prompt blueprint."""
        repo_root = Path(__file__).parent.parent.parent
        content = load_blueprint("system_prompt", repo_root)
        
        assert "Blueprint Agent" in content or "System Prompt" in content
    
    def test_load_character_sheet_blueprint(self):
        """Test loading character_sheet blueprint."""
        repo_root = Path(__file__).parent.parent.parent
        content = load_blueprint("character_sheet", repo_root)
        
        assert "Character Sheet" in content


class TestBuildOrchestratorPrompt:
    """Tests for build_orchestrator_prompt function."""
    
    def test_build_with_mode(self):
        """Test building orchestrator prompt with mode."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_orchestrator_prompt(
            "A dystopian detective",
            mode="NSFW",
            repo_root=repo_root
        )
        
        assert "RPBotGenerator" in system or "orchestrator" in system.lower()
        assert "Mode: NSFW" in user
        assert "SEED: A dystopian detective" in user
    
    def test_build_without_mode(self):
        """Test building orchestrator prompt without mode."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_orchestrator_prompt(
            "A cheerful baker",
            mode=None,
            repo_root=repo_root
        )
        
        assert "RPBotGenerator" in system or "orchestrator" in system.lower()
        assert "Mode:" not in user
        assert "SEED: A cheerful baker" in user
    
    def test_build_with_sfw_mode(self):
        """Test building with SFW mode."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_orchestrator_prompt(
            "A librarian",
            mode="SFW",
            repo_root=repo_root
        )
        
        assert "Mode: SFW" in user
        assert "SEED: A librarian" in user
    
    def test_build_with_platform_safe_mode(self):
        """Test building with Platform-Safe mode."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_orchestrator_prompt(
            "A warrior",
            mode="Platform-Safe",
            repo_root=repo_root
        )
        
        assert "Mode: Platform-Safe" in user


class TestBuildAssetPrompt:
    """Tests for build_asset_prompt function."""
    
    def test_build_system_prompt_asset(self):
        """Test building system_prompt asset."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_asset_prompt(
            "system_prompt",
            "A noir detective",
            mode="NSFW",
            repo_root=repo_root
        )
        
        assert "System Prompt" in system or "Blueprint Agent" in system
        assert "Mode: NSFW" in user
        assert "SEED: A noir detective" in user
    
    def test_build_without_mode(self):
        """Test building asset without mode."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_asset_prompt(
            "character_sheet",
            "A pirate captain",
            mode=None,
            repo_root=repo_root
        )
        
        assert "Character Sheet" in system or "Blueprint Agent" in system
        assert "Mode:" not in user
        assert "SEED: A pirate captain" in user
    
    def test_build_with_prior_assets(self):
        """Test building with prior assets for context."""
        repo_root = Path(__file__).parent.parent.parent
        prior = {
            "system_prompt": "You are a detective named Jake.",
            "post_history": "Jake is investigating a murder case."
        }
        
        system, user = build_asset_prompt(
            "character_sheet",
            "A noir detective",
            mode="NSFW",
            prior_assets=prior,
            repo_root=repo_root
        )
        
        assert "Prior Assets" in user
        assert "system_prompt" in user
        assert "Jake" in user
        assert "post_history" in user
        assert "murder case" in user
    
    def test_build_without_prior_assets(self):
        """Test building without prior assets."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_asset_prompt(
            "system_prompt",
            "A chef",
            mode="SFW",
            prior_assets=None,
            repo_root=repo_root
        )
        
        assert "Prior Assets" not in user
    
    def test_build_intro_scene_asset(self):
        """Test building intro_scene asset."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_asset_prompt(
            "intro_scene",
            "A space explorer",
            repo_root=repo_root
        )
        
        assert "Intro Scene" in system or "Blueprint Agent" in system


class TestBuildSeedgenPrompt:
    """Tests for build_seedgen_prompt function."""
    
    def test_build_seedgen_simple(self):
        """Test building seed generator prompt."""
        repo_root = Path(__file__).parent.parent.parent
        genre_lines = "Cyberpunk\nNoir\nDetective"
        
        system, user = build_seedgen_prompt(genre_lines, repo_root)
        
        assert "seed" in system.lower() or "generator" in system.lower()
        assert user == genre_lines
    
    def test_build_seedgen_multiline(self):
        """Test seed generator with multiline input."""
        repo_root = Path(__file__).parent.parent.parent
        genre_lines = """Fantasy
Romance
Medieval setting
Forbidden love"""
        
        system, user = build_seedgen_prompt(genre_lines, repo_root)
        
        assert user == genre_lines
        assert "Fantasy" in user
        assert "Medieval" in user
    
    def test_build_seedgen_missing_file(self, tmp_path):
        """Test seed generator with missing file."""
        with pytest.raises(FileNotFoundError):
            build_seedgen_prompt("test", tmp_path)


class TestPromptingEdgeCases:
    """Tests for edge cases in prompting."""
    
    def test_empty_seed(self):
        """Test with empty seed."""
        repo_root = Path(__file__).parent.parent.parent
        system, user = build_orchestrator_prompt("", repo_root=repo_root)
        
        assert "SEED: " in user
    
    def test_multiline_seed(self):
        """Test with multiline seed."""
        repo_root = Path(__file__).parent.parent.parent
        seed = """A detective
with a dark past
and a vendetta"""
        
        system, user = build_orchestrator_prompt(seed, repo_root=repo_root)
        
        assert seed in user
    
    def test_special_characters_in_seed(self):
        """Test seed with special characters."""
        repo_root = Path(__file__).parent.parent.parent
        seed = "A detective with $pecial ch@racters & symbols!"
        
        system, user = build_orchestrator_prompt(seed, repo_root=repo_root)
        
        assert seed in user
    
    def test_very_long_seed(self):
        """Test with very long seed."""
        repo_root = Path(__file__).parent.parent.parent
        seed = "A detective " * 100
        
        system, user = build_orchestrator_prompt(seed, repo_root=repo_root)
        
        assert seed in user
