"""Tests for enhanced similarity features (LLM and meta analysis)."""

import pytest
from pathlib import Path
from bpui.similarity import (
    CharacterProfile,
    LLMAnalysis,
    MetaAnalysis,
    SimilarityResult,
    SimilarityAnalyzer,
)


class TestCharacterProfile:
    """Test CharacterProfile class."""
    
    def test_from_assets_basic(self, sample_assets):
        """Test profile extraction from assets."""
        profile = CharacterProfile.from_assets(sample_assets)
        
        assert profile is not None
        assert isinstance(profile, CharacterProfile)
    
    def test_from_assets_extracts_name(self, sample_assets):
        """Test that name is extracted from character sheet."""
        profile = CharacterProfile.from_assets(sample_assets)
        
        # Name should be extracted from character sheet
        assert profile.name is not None
    
    def test_from_assets_default_values(self):
        """Test default values for empty assets."""
        profile = CharacterProfile.from_assets({})
        
        assert profile.name == ""
        assert profile.species == "human"
        assert profile.power_level == "unknown"
        assert profile.role == "unknown"
        # Mode defaults to SFW for empty assets (no NSFW markers found)
        assert profile.mode == "SFW"
    
    def test_to_dict(self):
        """Test profile conversion to dictionary."""
        profile = CharacterProfile(
            name="Test Character",
            age=25,
            gender="male",
            species="elf",
            personality_traits=["brave", "kind"],
            core_values=["justice", "mercy"],
        )
        
        data = profile.to_dict()
        
        assert data["name"] == "Test Character"
        assert data["age"] == 25
        assert data["gender"] == "male"
        assert data["species"] == "elf"
        assert data["personality_traits"] == ["brave", "kind"]
        assert data["core_values"] == ["justice", "mercy"]


class TestLLMAnalysis:
    """Test LLMAnalysis dataclass."""
    
    def test_llm_analysis_creation(self):
        """Test LLMAnalysis object creation."""
        analysis = LLMAnalysis(
            narrative_dynamics="These characters clash dramatically.",
            story_opportunities=["Redemption arc", "Betrayal"],
            scene_suggestions=["Scene 1", "Scene 2"],
            dialogue_style="Sharp, confrontational",
            relationship_arc="Enemies to allies",
        )
        
        assert analysis.narrative_dynamics == "These characters clash dramatically."
        assert len(analysis.story_opportunities) == 2
        assert len(analysis.scene_suggestions) == 2
        assert analysis.dialogue_style == "Sharp, confrontational"
        assert analysis.relationship_arc == "Enemies to allies"
    
    def test_llm_analysis_defaults(self):
        """Test LLMAnalysis default values."""
        analysis = LLMAnalysis()
        
        assert analysis.narrative_dynamics == ""
        assert analysis.story_opportunities == []
        assert analysis.scene_suggestions == []
        assert analysis.dialogue_style == ""
        assert analysis.relationship_arc == ""
    
    def test_llm_analysis_to_dict(self):
        """Test LLMAnalysis conversion to dictionary."""
        analysis = LLMAnalysis(
            narrative_dynamics="Test dynamics",
            story_opportunities=["Opportunity 1"],
        )
        
        data = analysis.to_dict()
        
        assert data["narrative_dynamics"] == "Test dynamics"
        assert data["story_opportunities"] == ["Opportunity 1"]


class TestMetaAnalysis:
    """Test MetaAnalysis dataclass."""
    
    def test_meta_analysis_creation(self):
        """Test MetaAnalysis object creation."""
        analysis = MetaAnalysis(
            redundancy_level="high",
            redundancy_score=0.85,
            issues_detected=["Shared traits", "Same occupation"],
            rework_suggestions_char1=["Change trait A"],
            rework_suggestions_char2=["Change trait B"],
            merge_recommendation="Consider merging",
            uniqueness_score=0.15,
        )
        
        assert analysis.redundancy_level == "high"
        assert analysis.redundancy_score == 0.85
        assert len(analysis.issues_detected) == 2
        assert len(analysis.rework_suggestions_char1) == 1
        assert len(analysis.rework_suggestions_char2) == 1
        assert analysis.merge_recommendation == "Consider merging"
        assert analysis.uniqueness_score == 0.15
    
    def test_meta_analysis_defaults(self):
        """Test MetaAnalysis default values."""
        analysis = MetaAnalysis()
        
        assert analysis.redundancy_level == "low"
        assert analysis.redundancy_score == 0.0
        assert analysis.issues_detected == []
        assert analysis.rework_suggestions_char1 == []
        assert analysis.rework_suggestions_char2 == []
        assert analysis.merge_recommendation is None
        assert analysis.uniqueness_score == 1.0
    
    def test_meta_analysis_to_dict(self):
        """Test MetaAnalysis conversion to dictionary."""
        analysis = MetaAnalysis(
            redundancy_level="extreme",
            redundancy_score=0.95,
        )
        
        data = analysis.to_dict()
        
        assert data["redundancy_level"] == "extreme"
        assert data["redundancy_score"] == 0.95


class TestSimilarityResultEnhanced:
    """Test SimilarityResult with enhanced features."""
    
    def test_similarity_result_with_llm_analysis(self):
        """Test SimilarityResult with LLM analysis."""
        llm_analysis = LLMAnalysis(
            narrative_dynamics="Test dynamics",
        )
        
        result = SimilarityResult(
            character1_name="Char1",
            character2_name="Char2",
            overall_score=0.5,
            llm_analysis=llm_analysis,
        )
        
        assert result.llm_analysis is not None
        assert result.llm_analysis.narrative_dynamics == "Test dynamics"
    
    def test_similarity_result_with_meta_analysis(self):
        """Test SimilarityResult with meta analysis."""
        meta_analysis = MetaAnalysis(
            redundancy_level="medium",
            redundancy_score=0.75,
        )
        
        result = SimilarityResult(
            character1_name="Char1",
            character2_name="Char2",
            overall_score=0.75,
            meta_analysis=meta_analysis,
        )
        
        assert result.meta_analysis is not None
        assert result.meta_analysis.redundancy_level == "medium"
    
    def test_similarity_result_to_dict_with_both(self):
        """Test SimilarityResult conversion with both analyses."""
        llm_analysis = LLMAnalysis(narrative_dynamics="Test")
        meta_analysis = MetaAnalysis(redundancy_level="high")
        
        result = SimilarityResult(
            character1_name="Char1",
            character2_name="Char2",
            overall_score=0.85,
            llm_analysis=llm_analysis,
            meta_analysis=meta_analysis,
        )
        
        data = result.to_dict()
        
        assert "llm_analysis" in data
        assert "meta_analysis" in data
        assert data["llm_analysis"]["narrative_dynamics"] == "Test"
        assert data["meta_analysis"]["redundancy_level"] == "high"


class TestRedundancyDetection:
    """Test redundancy detection logic."""
    
    def test_detect_redundancy_issues_identical_traits(self):
        """Test detection of identical traits."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind", "loyal"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind", "loyal", "smart"],
        )
        
        issues = analyzer._detect_redundancy_issues(profile1, profile2, 0.8)
        
        assert len(issues) > 0
        assert any("personality traits" in issue.lower() for issue in issues)
    
    def test_detect_redundancy_issues_identical_occupation(self):
        """Test detection of identical occupations."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            occupation="warrior",
        )
        profile2 = CharacterProfile(
            name="Char2",
            occupation="warrior",
        )
        
        issues = analyzer._detect_redundancy_issues(profile1, profile2, 0.6)
        
        assert len(issues) > 0
        assert any("warrior" in issue.lower() for issue in issues)
    
    def test_detect_redundancy_issues_no_redundancy(self):
        """Test that no issues are detected for different characters."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave"],
            occupation="warrior",
            species="human",
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["cautious"],
            occupation="scholar",
            species="elf",
        )
        
        issues = analyzer._detect_redundancy_issues(profile1, profile2, 0.2)
        
        # Should have minimal or no issues
        assert len(issues) == 0


class TestReworkSuggestions:
    """Test rework suggestion generation."""
    
    def test_generate_rework_suggestions_for_char1(self):
        """Test rework suggestions for character 1."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind", "loyal"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind", "loyal"],
        )
        
        suggestions = analyzer._generate_rework_suggestions(profile1, profile2, "char1")
        
        assert len(suggestions) > 0
        assert any("change" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_rework_suggestions_alternative_traits(self):
        """Test that alternative traits are suggested."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind"],
        )
        
        suggestions = analyzer._generate_rework_suggestions(profile1, profile2, "char1")
        
        # Should suggest alternatives like "reckless" instead of "brave"
        combined = " ".join(suggestions).lower()
        assert "reckless" in combined or "cautious" in combined


class TestMergeRecommendation:
    """Test merge recommendation generation."""
    
    def test_generate_merge_recommendation_more_developed_primary(self):
        """Test that more developed character becomes primary."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["a", "b", "c", "d", "e"],  # More developed
            background_keywords=["x", "y", "z"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["a", "b"],  # Less developed
            background_keywords=["x"],
        )
        
        recommendation = analyzer._generate_merge_recommendation(profile1, profile2)
        
        assert "Char1" in recommendation
        assert "more developed" in recommendation.lower()
    
    def test_generate_merge_recommendation_includes_unique_elements(self):
        """Test that unique elements from secondary are included."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind"],
            core_values=["justice"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "smart"],  # Unique: smart
            core_values=["justice", "loyalty"],  # Unique: loyalty
        )
        
        recommendation = analyzer._generate_merge_recommendation(profile1, profile2)
        
        assert "Char2" in recommendation
        # Should mention unique traits/values
        assert "smart" in recommendation.lower() or "loyalty" in recommendation.lower()


class TestRedundancyAnalysis:
    """Test full redundancy analysis."""
    
    def test_analyze_redundancy_extreme_level(self):
        """Test extreme redundancy detection (95%+)."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["justice", "mercy"],
            occupation="warrior",
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["justice", "mercy"],
            occupation="warrior",
        )
        
        meta = analyzer._analyze_redundancy(profile1, profile2, 0.96)
        
        assert meta.redundancy_level == "extreme"
        assert meta.redundancy_score == 0.96
        assert meta.merge_recommendation is not None
        assert meta.uniqueness_score < 0.1
    
    def test_analyze_redundancy_high_level(self):
        """Test high redundancy detection (85-95%)."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["justice", "mercy"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["justice", "mercy"],
        )
        
        meta = analyzer._analyze_redundancy(profile1, profile2, 0.88)
        
        assert meta.redundancy_level == "high"
        assert meta.redundancy_score == 0.88
        assert meta.merge_recommendation is None  # No merge for high, only extreme
    
    def test_analyze_redundancy_medium_level(self):
        """Test medium redundancy detection (75-85%)."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave", "kind"],
            core_values=["justice"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["brave", "kind", "loyal"],
            core_values=["justice", "mercy"],
        )
        
        meta = analyzer._analyze_redundancy(profile1, profile2, 0.78)
        
        assert meta.redundancy_level == "medium"
        assert meta.redundancy_score == 0.78
    
    def test_analyze_redundancy_low_level(self):
        """Test low redundancy detection (<75%)."""
        analyzer = SimilarityAnalyzer()
        
        profile1 = CharacterProfile(
            name="Char1",
            personality_traits=["brave"],
            core_values=["justice"],
        )
        profile2 = CharacterProfile(
            name="Char2",
            personality_traits=["cautious"],
            core_values=["mercy"],
        )
        
        meta = analyzer._analyze_redundancy(profile1, profile2, 0.4)
        
        assert meta.redundancy_level == "low"
        assert meta.redundancy_score == 0.4
        assert meta.uniqueness_score > 0.5


class TestLLMComparison:
    """Test LLM-powered comparison."""
    
    def test_parse_llm_response_json(self):
        """Test parsing JSON LLM response."""
        analyzer = SimilarityAnalyzer()
        
        json_response = """{
            "narrative_dynamics": "Test dynamics",
            "story_opportunities": ["Op1", "Op2"],
            "scene_suggestions": ["Scene1"],
            "dialogue_style": "Test style",
            "relationship_arc": "Test arc"
        }"""
        
        analysis = analyzer._parse_llm_response(json_response)
        
        assert analysis is not None
        assert analysis.narrative_dynamics == "Test dynamics"
        assert len(analysis.story_opportunities) == 2
        assert analysis.dialogue_style == "Test style"
    
    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON (fallback to text)."""
        analyzer = SimilarityAnalyzer()
        
        text_response = "This is not JSON"
        
        analysis = analyzer._parse_llm_response(text_response)
        
        assert analysis is not None
        # Should use text fallback
        assert analysis.narrative_dynamics == "This is not JSON"[:500]
        assert analysis.story_opportunities == []
    
    def test_parse_llm_response_partial_json(self):
        """Test parsing partial JSON with missing fields."""
        analyzer = SimilarityAnalyzer()
        
        partial_response = """{
            "narrative_dynamics": "Test dynamics"
        }"""
        
        analysis = analyzer._parse_llm_response(partial_response)
        
        assert analysis is not None
        assert analysis.narrative_dynamics == "Test dynamics"
        # Missing fields should have defaults
        assert analysis.story_opportunities == []
        assert analysis.scene_suggestions == []


@pytest.fixture
def sample_assets():
    """Provide sample character assets for testing."""
    return {
        "character_sheet": """
Name: Test Character
Age: 25
Gender: Male
Species: Human
Occupation: Warrior

Personality:
- Brave
- Kind
- Loyal

Values:
- Justice
- Mercy

Motivation: Protect the innocent
""",
        "system_prompt": "You are Test Character, a brave warrior.",
        "post_history": "Test post history content.",
    }