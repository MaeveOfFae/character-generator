"""Unit tests for similarity analyzer module."""

import pytest
from pathlib import Path
from bpui.similarity import CharacterProfile, SimilarityAnalyzer, SimilarityResult


class TestCharacterProfile:
    """Test CharacterProfile extraction."""
    
    def test_from_assets_basic(self):
        """Test basic profile extraction."""
        assets = {
            "character_sheet": """
Name: Test Character
Age: 25
Gender: Female
Species: Human
Occupation: Engineer

Personality: Intelligent, curious, adventurous

Values: Honesty, loyalty, courage
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile = CharacterProfile.from_assets(assets)
        
        assert profile.name == "Test Character"
        assert profile.age == 25
        assert profile.gender == "Female"
        assert profile.species == "human"
        assert profile.occupation == "Engineer"
    
    def test_extract_traits(self):
        """Test personality trait extraction."""
        assets = {
            "character_sheet": """
Name: Alice
Personality: Brave, kind, resourceful, witty
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile = CharacterProfile.from_assets(assets)
        
        # Should extract personality traits
        assert len(profile.personality_traits) > 0
        assert "brave" in [t.lower() for t in profile.personality_traits]
    
    def test_extract_values(self):
        """Test value extraction."""
        assets = {
            "character_sheet": """
Name: Bob
Values: Justice, freedom, compassion
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile = CharacterProfile.from_assets(assets)
        
        assert len(profile.core_values) > 0
        assert any("justice" in v.lower() for v in profile.core_values)
    
    def test_power_level_detection(self):
        """Test power level detection."""
        # High power
        assets_high = {
            "character_sheet": """
Name: Godlike Entity
This character is a supreme deity with ultimate power.
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_high = CharacterProfile.from_assets(assets_high)
        assert profile_high.power_level == "high"
        
        # Low power
        assets_low = {
            "character_sheet": """
Name: Ordinary Person
This is a normal average human with no special abilities.
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_low = CharacterProfile.from_assets(assets_low)
        assert profile_low.power_level == "low"
    
    def test_role_detection(self):
        """Test role detection."""
        # Protagonist
        assets_hero = {
            "character_sheet": """
Name: Hero
The main hero protagonist of the story.
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_hero = CharacterProfile.from_assets(assets_hero)
        assert profile_hero.role == "protagonist"
        
        # Antagonist
        assets_villain = {
            "character_sheet": """
Name: Villain
The main antagonist and enemy.
            """.strip(),
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_villain = CharacterProfile.from_assets(assets_villain)
        assert profile_villain.role == "antagonist"
    
    def test_mode_detection(self):
        """Test mode detection."""
        # NSFW
        assets_nsfw = {
            "character_sheet": "Name: Test\n\nNSFW content here.",
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_nsfw = CharacterProfile.from_assets(assets_nsfw)
        assert profile_nsfw.mode == "NSFW"
        
        # Platform-Safe
        assets_safe = {
            "character_sheet": "Name: Test\n\nPlatform-Safe content.",
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_safe = CharacterProfile.from_assets(assets_safe)
        assert profile_safe.mode == "Platform-Safe"
        
        # SFW (default)
        assets_sfw = {
            "character_sheet": "Name: Test",
            "system_prompt": "",
            "post_history": "",
        }
        
        profile_sfw = CharacterProfile.from_assets(assets_sfw)
        assert profile_sfw.mode == "SFW"


class TestSimilarityAnalyzer:
    """Test SimilarityAnalyzer functionality."""
    
    def test_compare_lists(self):
        """Test list comparison (Jaccard index)."""
        analyzer = SimilarityAnalyzer()
        
        # Identical lists
        list1 = ["brave", "kind", "loyal"]
        list2 = ["brave", "kind", "loyal"]
        
        similarity = analyzer._compare_lists(list1, list2)
        assert similarity == 1.0
        
        # No overlap
        list3 = ["brave", "kind", "loyal"]
        list4 = ["cowardly", "mean", "treacherous"]
        
        similarity = analyzer._compare_lists(list3, list4)
        assert similarity == 0.0
        
        # Partial overlap
        list5 = ["brave", "kind", "loyal"]
        list6 = ["brave", "smart", "loyal"]
        
        similarity = analyzer._compare_lists(list5, list6)
        assert 0 < similarity < 1
        assert similarity == 2/3  # 2 shared out of 3 unique
    
    def test_compare_profiles(self):
        """Test profile comparison."""
        profile1 = CharacterProfile(
            name="Alice",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["honesty", "justice"],
            goals=["save the world"],
        )
        
        profile2 = CharacterProfile(
            name="Bob",
            personality_traits=["brave", "smart", "loyal"],
            core_values=["honesty", "justice"],
            goals=["find treasure"],
        )
        
        analyzer = SimilarityAnalyzer()
        result = analyzer.compare_profiles(profile1, profile2)
        
        assert isinstance(result, SimilarityResult)
        assert result.character1_name == "Alice"
        assert result.character2_name == "Bob"
        assert 0 <= result.overall_score <= 1
        assert result.compatibility in ["high", "medium", "low", "conflict"]
    
    def test_find_commonalities(self):
        """Test finding commonalities between profiles."""
        profile1 = CharacterProfile(
            name="Alice",
            personality_traits=["brave", "kind"],
            core_values=["honesty", "justice"],
            species="human",
        )
        
        profile2 = CharacterProfile(
            name="Bob",
            personality_traits=["brave", "smart"],
            core_values=["honesty", "freedom"],
            species="human",
        )
        
        analyzer = SimilarityAnalyzer()
        commonalities = analyzer._find_commonalities(profile1, profile2)
        
        assert len(commonalities) > 0
        # Should mention shared species
        assert any("human" in c.lower() for c in commonalities)
    
    def test_find_differences(self):
        """Test finding differences between profiles."""
        profile1 = CharacterProfile(
            name="Alice",
            species="human",
            role="protagonist",
            personality_traits=["brave"],
        )
        
        profile2 = CharacterProfile(
            name="Bob",
            species="elf",
            role="supporting",
            personality_traits=["smart", "wise"],
        )
        
        analyzer = SimilarityAnalyzer()
        differences = analyzer._find_differences(profile1, profile2)
        
        assert len(differences) > 0
        # Should mention different species
        assert any("species" in d.lower() for d in differences)
    
    def test_assess_compatibility(self):
        """Test compatibility assessment."""
        # Similar profiles = high compatibility
        profile1 = CharacterProfile(
            name="Alice",
            personality_traits=["brave", "kind"],
            core_values=["honesty", "justice"],
            role="protagonist",
        )
        
        profile2 = CharacterProfile(
            name="Bob",
            personality_traits=["brave", "kind"],
            core_values=["honesty", "justice"],
            role="protagonist",
        )
        
        analyzer = SimilarityAnalyzer()
        compatibility = analyzer._assess_compatibility(profile1, profile2, 0.8)
        
        assert compatibility == "high"
        
        # Conflicting values = conflict
        profile3 = CharacterProfile(
            name="Villain",
            core_values=["deception", "cruelty"],
            role="antagonist",
        )
        
        profile4 = CharacterProfile(
            name="Hero",
            core_values=["honesty", "mercy"],
            role="protagonist",
        )
        
        compatibility2 = analyzer._assess_compatibility(profile3, profile4, 0.3)
        
        assert compatibility2 in ["conflict", "low"]
    
    def test_calculate_conflict_potential(self):
        """Test conflict potential calculation."""
        # Hero vs villain
        profile1 = CharacterProfile(
            name="Hero",
            role="protagonist",
            core_values=["honesty", "mercy"],
            power_level="high",
        )
        
        profile2 = CharacterProfile(
            name="Villain",
            role="antagonist",
            core_values=["deception", "cruelty"],
            power_level="high",
        )
        
        analyzer = SimilarityAnalyzer()
        conflict = analyzer._calculate_conflict_potential(profile1, profile2)
        
        assert conflict > 0.5  # Should have high conflict potential
    
    def test_calculate_synergy_potential(self):
        """Test synergy potential calculation."""
        # Protagonist + supporting character
        profile1 = CharacterProfile(
            name="Hero",
            role="protagonist",
            goals=["save the world"],
        )
        
        profile2 = CharacterProfile(
            name="Sidekick",
            role="supporting",
            goals=["save the world"],
        )
        
        analyzer = SimilarityAnalyzer()
        synergy = analyzer._calculate_synergy_potential(profile1, profile2)
        
        assert synergy > 0.4  # Should have decent synergy


class TestSimilarityResult:
    """Test SimilarityResult dataclass."""
    
    def test_to_dict(self):
        """Test result conversion to dictionary."""
        result = SimilarityResult(
            character1_name="Alice",
            character2_name="Bob",
            overall_score=0.75,
            compatibility="high",
            conflict_potential=0.1,
            synergy_potential=0.8,
            commonalities=["Both are brave"],
            differences=["Alice is human, Bob is elf"],
            relationship_suggestions=["They would make good allies"],
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["character1_name"] == "Alice"
        assert result_dict["character2_name"] == "Bob"
        assert result_dict["overall_score"] == 0.75
        assert result_dict["compatibility"] == "high"
        assert len(result_dict["commonalities"]) == 1
        assert len(result_dict["differences"]) == 1