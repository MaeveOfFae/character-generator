"""Character similarity analyzer module.

Analyzes similarities and differences between character drafts
based on extracted profiles from character sheets and other assets.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter


@dataclass
class CharacterProfile:
    """Extracted profile from character assets."""
    
    # Basic info
    name: str = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    species: str = "human"
    
    # Personality traits (extracted from character sheet)
    personality_traits: List[str] = field(default_factory=list)
    core_values: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    
    # Physical/appearance
    appearance_keywords: List[str] = field(default_factory=list)
    
    # Background/story elements
    occupation: Optional[str] = None
    background_keywords: List[str] = field(default_factory=list)
    setting: Optional[str] = None
    
    # Power dynamics
    power_level: str = "unknown"  # high, medium, low, unknown
    role: str = "unknown"
    
    # Content mode
    mode: str = "unknown"
    
    @classmethod
    def from_assets(cls, assets: Dict[str, str]) -> 'CharacterProfile':
        """Extract profile from character assets.
        
        Args:
            assets: Dictionary of asset names to content
            
        Returns:
            CharacterProfile with extracted data
        """
        profile = cls()
        
        # Get character sheet (primary source)
        char_sheet = assets.get("character_sheet", "")
        system_prompt = assets.get("system_prompt", "")
        post_history = assets.get("post_history", "")
        
        # Extract from character sheet
        profile._extract_from_character_sheet(char_sheet)
        
        # Extract from system prompt
        profile._extract_from_system_prompt(system_prompt)
        
        # Extract from post history
        profile._extract_from_post_history(post_history)
        
        # Extract mode
        if "NSFW" in char_sheet or "NSFW" in system_prompt:
            profile.mode = "NSFW"
        elif "Platform-Safe" in char_sheet or "Platform-Safe" in system_prompt:
            profile.mode = "Platform-Safe"
        else:
            profile.mode = "SFW"
        
        return profile
    
    def _extract_from_character_sheet(self, text: str) -> None:
        """Extract information from character sheet."""
        # Extract name
        name_match = re.search(r'(?:Name|Character)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if name_match:
            self.name = name_match.group(1).strip()
        
        # Extract age
        age_match = re.search(r'(?:Age)[:\s]+(\d+)', text, re.IGNORECASE)
        if age_match:
            self.age = int(age_match.group(1))
        
        # Extract gender
        gender_match = re.search(r'(?:Gender|Sex)[:\s]+([^\n,]+)', text, re.IGNORECASE)
        if gender_match:
            self.gender = gender_match.group(1).strip()
        
        # Extract species/ancestry
        species_patterns = [
            r'(?:Species|Race|Ancestry)[:\s]+([^\n,]+)',
            r'(?:Moreau|Morphosis)[:\s]+([^\n,]+)',
        ]
        for pattern in species_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.species = match.group(1).strip().lower()
                break
        
        # Extract occupation
        occupation_match = re.search(
            r'(?:Occupation|Job|Role|Profession)[:\s]+([^\n,]+)',
            text, re.IGNORECASE
        )
        if occupation_match:
            self.occupation = occupation_match.group(1).strip()
        
        # Extract personality traits
        personality_section = self._extract_section(text, ['personality', 'traits', 'nature'])
        self.personality_traits = self._extract_keywords(personality_section)
        
        # Extract values
        values_section = self._extract_section(text, ['values', 'beliefs', 'principles'])
        self.core_values = self._extract_keywords(values_section)
        
        # Extract motivations
        motivation_section = self._extract_section(text, ['motivation', 'drive', 'motives'])
        self.motivations = self._extract_keywords(motivation_section)
        
        # Extract goals
        goals_section = self._extract_section(text, ['goal', 'objective', 'ambition'])
        self.goals = self._extract_keywords(goals_section)
        
        # Extract fears
        fears_section = self._extract_section(text, ['fear', 'phobia', 'weakness'])
        self.fears = self._extract_keywords(fears_section)
        
        # Extract appearance
        appearance_section = self._extract_section(text, ['appearance', 'looks', 'description'])
        self.appearance_keywords = self._extract_keywords(appearance_section)
        
        # Extract background
        background_section = self._extract_section(text, ['background', 'history', 'backstory'])
        self.background_keywords = self._extract_keywords(background_section)
        
        # Extract setting
        setting_match = re.search(r'(?:Setting|World|Location)[:\s]+([^\n,]+)', text, re.IGNORECASE)
        if setting_match:
            self.setting = setting_match.group(1).strip()
        
        # Determine power level
        power_keywords = {
            'high': ['god', 'demi-god', 'deity', 'immortal', 'supreme', 'ultimate', 'transcendent'],
            'medium': ['powerful', 'strong', 'skilled', 'expert', 'master', 'elite'],
            'low': ['weak', 'helpless', 'powerless', 'ordinary', 'normal', 'average'],
        }
        text_lower = text.lower()
        for level, keywords in power_keywords.items():
            if any(kw in text_lower for kw in keywords):
                self.power_level = level
                break
        
        # Determine role
        role_patterns = {
            'protagonist': ['hero', 'protagonist', 'main character', 'lead'],
            'antagonist': ['villain', 'antagonist', 'enemy', 'opponent'],
            'supporting': ['sidekick', 'companion', 'friend', 'ally', 'support'],
            'neutral': ['neutral', 'bystander', 'observer', 'witness'],
        }
        text_lower = text.lower()
        for role, patterns in role_patterns.items():
            if any(p in text_lower for p in patterns):
                self.role = role
                break
    
    def _extract_from_system_prompt(self, text: str) -> None:
        """Extract additional info from system prompt."""
        # System prompt often reinforces key traits
        # Extract additional personality traits
        for line in text.split('\n'):
            if len(line) > 5 and len(line) < 100:
                # Look for trait-like sentences
                if any(word in line.lower() for word in ['is', 'tends to', 'often', 'always', 'never']):
                    self.personality_traits.append(line.strip())
    
    def _extract_from_post_history(self, text: str) -> None:
        """Extract behavior patterns from post history."""
        # Post history shows actual behavior patterns
        # Extract behavioral keywords
        keywords = []
        for line in text.split('\n'):
            words = line.lower().split()
            keywords.extend([w.strip('.,!?;:') for w in words if len(w) > 3])
        
        # Add unique keywords to personality traits
        unique_keywords = list(set(keywords))[:20]  # Limit to 20
        self.personality_traits.extend(unique_keywords)
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """Extract a section from text based on keywords.
        
        Args:
            text: Full text to search
            keywords: Section header keywords
            
        Returns:
            Extracted section text
        """
        lines = text.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            # Check if this line starts a section
            if any(kw in line.lower() for kw in keywords):
                in_section = True
                continue
            
            # Stop if we hit another major section
            if in_section and line.strip() and re.match(r'^[A-Z][^:]+:', line):
                break
            
            if in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            List of keywords
        """
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'it', 'its', 'who', 'whom', 'whose', 'which', 'what',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now'
        }
        
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Return unique keywords, limited
        return list(set(keywords))[:30]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'species': self.species,
            'personality_traits': self.personality_traits,
            'core_values': self.core_values,
            'motivations': self.motivations,
            'goals': self.goals,
            'fears': self.fears,
            'appearance_keywords': self.appearance_keywords,
            'occupation': self.occupation,
            'background_keywords': self.background_keywords,
            'setting': self.setting,
            'power_level': self.power_level,
            'role': self.role,
            'mode': self.mode,
        }


@dataclass
class LLMAnalysis:
    """LLM-powered deep analysis of character relationship."""
    
    # Narrative dynamics
    narrative_dynamics: str = ""
    
    # Story opportunities
    story_opportunities: List[str] = field(default_factory=list)
    
    # Scene suggestions
    scene_suggestions: List[str] = field(default_factory=list)
    
    # Dialogue style analysis
    dialogue_style: str = ""
    
    # Relationship arc suggestions
    relationship_arc: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'narrative_dynamics': self.narrative_dynamics,
            'story_opportunities': self.story_opportunities,
            'scene_suggestions': self.scene_suggestions,
            'dialogue_style': self.dialogue_style,
            'relationship_arc': self.relationship_arc,
        }


@dataclass
class MetaAnalysis:
    """Meta analysis of character redundancy and rework potential."""
    
    # Redundancy assessment
    redundancy_level: str = "low"  # low, medium, high, extreme
    redundancy_score: float = 0.0  # 0-1
    
    # Issues detected
    issues_detected: List[str] = field(default_factory=list)
    
    # Rework suggestions for character 1
    rework_suggestions_char1: List[str] = field(default_factory=list)
    
    # Rework suggestions for character 2
    rework_suggestions_char2: List[str] = field(default_factory=list)
    
    # Merge recommendation
    merge_recommendation: Optional[str] = None
    
    # Uniqueness score
    uniqueness_score: float = 1.0  # 0-1, higher is more unique
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'redundancy_level': self.redundancy_level,
            'redundancy_score': self.redundancy_score,
            'issues_detected': self.issues_detected,
            'rework_suggestions_char1': self.rework_suggestions_char1,
            'rework_suggestions_char2': self.rework_suggestions_char2,
            'merge_recommendation': self.merge_recommendation,
            'uniqueness_score': self.uniqueness_score,
        }


@dataclass
class SimilarityResult:
    """Result of similarity comparison between two characters."""
    
    character1_name: str
    character2_name: str
    
    # Overall similarity score (0-1)
    overall_score: float
    
    # Dimension scores (0-1 each)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    
    # Compatibility assessment
    compatibility: str = "unknown"  # high, medium, low, conflict
    
    # Conflict potential (0-1)
    conflict_potential: float = 0.0
    
    # Synergy potential (0-1)
    synergy_potential: float = 0.0
    
    # Commonalities
    commonalities: List[str] = field(default_factory=list)
    
    # Differences
    differences: List[str] = field(default_factory=list)
    
    # Relationship suggestions
    relationship_suggestions: List[str] = field(default_factory=list)
    
    # LLM Deep Analysis (optional)
    llm_analysis: Optional['LLMAnalysis'] = None
    
    # Meta/Redundancy Analysis (optional)
    meta_analysis: Optional['MetaAnalysis'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result_dict = {
            'character1_name': self.character1_name,
            'character2_name': self.character2_name,
            'overall_score': self.overall_score,
            'dimension_scores': self.dimension_scores,
            'compatibility': self.compatibility,
            'conflict_potential': self.conflict_potential,
            'synergy_potential': self.synergy_potential,
            'commonalities': self.commonalities,
            'differences': self.differences,
            'relationship_suggestions': self.relationship_suggestions,
        }
        
        if self.llm_analysis:
            result_dict['llm_analysis'] = self.llm_analysis.to_dict()
        
        if self.meta_analysis:
            result_dict['meta_analysis'] = self.meta_analysis.to_dict()
        
        return result_dict


class SimilarityAnalyzer:
    """Analyze similarities and differences between characters."""
    
    def __init__(self):
        """Initialize similarity analyzer."""
        self.profiles: Dict[str, CharacterProfile] = {}
    
    def load_draft(self, draft_directory: Path) -> Optional[CharacterProfile]:
        """Load and profile a character draft.
        
        Args:
            draft_directory: Path to draft directory
            
        Returns:
            CharacterProfile or None if loading failed
        """
        from .pack_io import load_draft
        
        try:
            character_assets = load_draft(draft_directory)
            character_profile = CharacterProfile.from_assets(character_assets)
            
            # Use directory name if no name extracted
            if not character_profile.name:
                character_profile.name = draft_directory.name
            
            self.profiles[draft_directory.name] = character_profile
            return character_profile
            
        except Exception as e:
            print(f"Error loading {draft_directory.name}: {e}")
            return None
    
    def compare_profiles(
        self, 
        first_profile: CharacterProfile, 
        second_profile: CharacterProfile,
        use_llm: bool = False,
        llm_engine: Optional[Any] = None
    ) -> SimilarityResult:
        """Compare two character profiles.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            
        Returns:
            SimilarityResult with comparison data
            
        Args:
            use_llm: Whether to include LLM-powered deep analysis
            llm_engine: LLM engine instance for analysis (required if use_llm=True)
        """
        # Calculate dimension scores
        dimension_scores = {
            'personality': self._compare_lists(
                first_profile.personality_traits, second_profile.personality_traits
            ),
            'values': self._compare_lists(
                first_profile.core_values, second_profile.core_values
            ),
            'motivations': self._compare_lists(
                first_profile.motivations, second_profile.motivations
            ),
            'goals': self._compare_lists(
                first_profile.goals, second_profile.goals
            ),
            'background': self._compare_lists(
                first_profile.background_keywords, second_profile.background_keywords
            ),
        }
        
        # Calculate overall score (weighted average)
        weights = {
            'personality': 0.3,
            'values': 0.25,
            'motivations': 0.2,
            'goals': 0.15,
            'background': 0.1,
        }
        
        overall_score = sum(
            dimension_scores[dim] * weights[dim]
            for dim in dimension_scores
        )
        
        # Find commonalities
        character_commonalities = self._find_commonalities(first_profile, second_profile)
        
        # Find differences
        character_differences = self._find_differences(first_profile, second_profile)
        
        # Assess compatibility
        compatibility_level = self._assess_compatibility(first_profile, second_profile, overall_score)
        
        # Calculate conflict potential
        conflict_potential = self._calculate_conflict_potential(first_profile, second_profile)
        
        # Calculate synergy potential
        synergy_potential = self._calculate_synergy_potential(first_profile, second_profile)
        
        # Generate relationship suggestions
        relationship_suggestions = self._generate_relationship_suggestions(
            first_profile, second_profile, compatibility_level
        )
        
        result = SimilarityResult(
            character1_name=first_profile.name,
            character2_name=second_profile.name,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            compatibility=compatibility_level,
            conflict_potential=conflict_potential,
            synergy_potential=synergy_potential,
            commonalities=character_commonalities,
            differences=character_differences,
            relationship_suggestions=relationship_suggestions,
        )
        
        # Add LLM analysis if requested
        if use_llm and llm_engine:
            result.llm_analysis = self._compare_with_llm(first_profile, second_profile, llm_engine)
        
        # Always add meta analysis
        result.meta_analysis = self._analyze_redundancy(first_profile, second_profile, overall_score)
        
        return result
    
    def compare_drafts(
        self, 
        first_draft_path: Path, 
        second_draft_path: Path,
        use_llm: bool = False,
        llm_engine: Optional[Any] = None
    ) -> Optional[SimilarityResult]:
        """Compare two character drafts.
        
        Args:
            first_draft_path: Path to first draft
            second_draft_path: Path to second draft
            use_llm: Whether to include LLM-powered deep analysis
            llm_engine: LLM engine instance for analysis
            
        Returns:
            SimilarityResult or None if comparison failed
        """
        first_profile = self.load_draft(first_draft_path)
        second_profile = self.load_draft(second_draft_path)
        
        if not first_profile or not second_profile:
            return None
        
        return self.compare_profiles(first_profile, second_profile, use_llm, llm_engine)
    
    def compare_multiple(
        self, draft_dirs: List[Path]
    ) -> Dict[Tuple[str, str], SimilarityResult]:
        """Compare all pairs of characters.
        
        Args:
            draft_dirs: List of draft directory paths
            
        Returns:
            Dictionary of (name1, name2) tuples to SimilarityResult
        """
        results = {}
        
        # Load all profiles
        profiles = []
        for draft_dir in draft_dirs:
            profile = self.load_draft(draft_dir)
            if profile:
                profiles.append(profile)
        
        # Compare all pairs
        for i, profile1 in enumerate(profiles):
            for j, profile2 in enumerate(profiles):
                if i < j:  # Avoid duplicate comparisons
                    result = self.compare_profiles(profile1, profile2)
                    results[(profile1.name, profile2.name)] = result
        
        return results
    
    def cluster_characters(
        self, draft_dirs: List[Path], min_similarity: float = 0.6
    ) -> List[List[str]]:
        """Cluster similar characters.
        
        Args:
            draft_dirs: List of draft directory paths
            min_similarity: Minimum similarity threshold for clustering
            
        Returns:
            List of clusters (each cluster is a list of character names)
        """
        # Get all pairwise comparisons
        comparisons = self.compare_multiple(draft_dirs)
        
        # Build adjacency list
        adjacency = {}
        for (name1, name2), result in comparisons.items():
            if result.overall_score >= min_similarity:
                if name1 not in adjacency:
                    adjacency[name1] = []
                if name2 not in adjacency:
                    adjacency[name2] = []
                adjacency[name1].append(name2)
                adjacency[name2].append(name1)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        
        for name in adjacency:
            if name not in visited:
                cluster = []
                stack = [name]
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        cluster.append(current)
                        stack.extend(adjacency.get(current, []))
                
                if cluster:
                    clusters.append(cluster)
        
        return clusters
    
    def _compare_lists(self, list1: List[str], list2: List[str]) -> float:
        """Calculate similarity between two lists (Jaccard index).
        
        Args:
            list1: First list
            list2: Second list
            
        Returns:
            Similarity score (0-1)
        """
        set1 = set(list1)
        set2 = set(list2)
        
        if not set1 and not set2:
            return 1.0  # Both empty = identical
        
        if not set1 or not set2:
            return 0.0  # One empty = no similarity
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _find_commonalities(
        self, profile1: CharacterProfile, profile2: CharacterProfile
    ) -> List[str]:
        """Find commonalities between two profiles.
        
        Args:
            profile1: First profile
            profile2: Second profile
            
        Returns:
            List of commonalities
        """
        commonalities = []
        
        # Common traits
        common_traits = set(profile1.personality_traits) & set(profile2.personality_traits)
        if common_traits:
            commonalities.extend([f"Shared traits: {', '.join(list(common_traits)[:5])}"])
        
        # Common values
        common_values = set(profile1.core_values) & set(profile2.core_values)
        if common_values:
            commonalities.append(f"Shared values: {', '.join(list(common_values)[:3])}")
        
        # Common goals
        common_goals = set(profile1.goals) & set(profile2.goals)
        if common_goals:
            commonalities.append(f"Shared goals: {', '.join(list(common_goals)[:3])}")
        
        # Same species
        if profile1.species == profile2.species:
            commonalities.append(f"Same species: {profile1.species}")
        
        # Same setting
        if profile1.setting and profile2.setting and profile1.setting == profile2.setting:
            commonalities.append(f"Same setting: {profile1.setting}")
        
        # Same occupation
        if profile1.occupation and profile2.occupation and profile1.occupation == profile2.occupation:
            commonalities.append(f"Same occupation: {profile1.occupation}")
        
        return commonalities[:10]  # Limit to 10
    
    def _find_differences(
        self, profile1: CharacterProfile, profile2: CharacterProfile
    ) -> List[str]:
        """Find differences between two profiles.
        
        Args:
            profile1: First profile
            profile2: Second profile
            
        Returns:
            List of differences
        """
        differences = []
        
        # Different species
        if profile1.species != profile2.species:
            differences.append(f"Different species: {profile1.species} vs {profile2.species}")
        
        # Different power levels
        if profile1.power_level != profile2.power_level:
            differences.append(f"Different power: {profile1.power_level} vs {profile2.power_level}")
        
        # Different roles
        if profile1.role != profile2.role:
            differences.append(f"Different roles: {profile1.role} vs {profile2.role}")
        
        # Different occupations
        if profile1.occupation != profile2.occupation:
            occ1 = profile1.occupation or "none"
            occ2 = profile2.occupation or "none"
            differences.append(f"Different occupations: {occ1} vs {occ2}")
        
        # Unique traits for profile1
        unique_traits1 = set(profile1.personality_traits) - set(profile2.personality_traits)
        if unique_traits1:
            differences.append(f"{profile1.name} unique traits: {', '.join(list(unique_traits1)[:3])}")
        
        # Unique traits for profile2
        unique_traits2 = set(profile2.personality_traits) - set(profile1.personality_traits)
        if unique_traits2:
            differences.append(f"{profile2.name} unique traits: {', '.join(list(unique_traits2)[:3])}")
        
        return differences[:10]  # Limit to 10
    
    def _assess_compatibility(
        self, profile1: CharacterProfile, profile2: CharacterProfile, overall_score: float
    ) -> str:
        """Assess compatibility between two characters.
        
        Args:
            profile1: First profile
            profile2: Second profile
            overall_score: Overall similarity score
            
        Returns:
            Compatibility assessment (high, medium, low, conflict)
        """
        # Check for conflicting values
        conflicting_values = {
            ('honesty', 'deception'),
            ('loyalty', 'betrayal'),
            ('mercy', 'cruelty'),
            ('justice', 'corruption'),
        }
        
        values1 = set(profile1.core_values)
        values2 = set(profile2.core_values)
        
        for val1, val2 in conflicting_values:
            if val1 in values1 and val2 in values2:
                return "conflict"
            if val2 in values1 and val1 in values2:
                return "conflict"
        
        # Check roles
        if profile1.role == "antagonist" and profile2.role == "antagonist":
            return "low"  # Villains rarely work together
        
        # High similarity = high compatibility
        if overall_score >= 0.7:
            return "high"
        elif overall_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_conflict_potential(
        self, profile1: CharacterProfile, profile2: CharacterProfile
    ) -> float:
        """Calculate conflict potential between two characters.
        
        Args:
            profile1: First profile
            profile2: Second profile
            
        Returns:
            Conflict potential (0-1)
        """
        conflict_score = 0.0
        
        # Opposing roles
        if profile1.role == "antagonist" and profile2.role == "protagonist":
            conflict_score += 0.8
        elif profile1.role == "protagonist" and profile2.role == "antagonist":
            conflict_score += 0.8
        
        # Opposing power levels
        if profile1.power_level == "high" and profile2.power_level == "low":
            conflict_score += 0.3
        elif profile1.power_level == "low" and profile2.power_level == "high":
            conflict_score += 0.3
        
        # Opposing values
        values1 = set(profile1.core_values)
        values2 = set(profile2.core_values)
        
        opposing_pairs = {
            'honesty': ['deception', 'dishonesty'],
            'mercy': ['cruelty', 'ruthlessness'],
            'justice': ['injustice', 'corruption'],
            'freedom': ['control', 'oppression'],
        }
        
        for value, opposites in opposing_pairs.items():
            if value in values1 and any(op in values2 for op in opposites):
                conflict_score += 0.2
            if value in values2 and any(op in values1 for op in opposites):
                conflict_score += 0.2
        
        return min(conflict_score, 1.0)
    
    def _calculate_synergy_potential(
        self, profile1: CharacterProfile, profile2: CharacterProfile
    ) -> float:
        """Calculate synergy potential between two characters.
        
        Args:
            profile1: First profile
            profile2: Second profile
            
        Returns:
            Synergy potential (0-1)
        """
        synergy_score = 0.0
        
        # Complementary roles
        if profile1.role == "protagonist" and profile2.role == "supporting":
            synergy_score += 0.5
        elif profile2.role == "protagonist" and profile1.role == "supporting":
            synergy_score += 0.5
        
        # Complementary skills (based on keywords)
        skills1 = set(profile1.background_keywords)
        skills2 = set(profile2.background_keywords)
        
        # If they have different skills, potential for teamwork
        if skills1 and skills2:
            overlap = len(skills1 & skills2) / len(skills1 | skills2)
            synergy_score += (1.0 - overlap) * 0.3
        
        # Shared goals
        if profile1.goals and profile2.goals:
            shared_goals = set(profile1.goals) & set(profile2.goals)
            if shared_goals:
                synergy_score += 0.3
        
        return min(synergy_score, 1.0)
    
    def _generate_relationship_suggestions(
        self, profile1: CharacterProfile, profile2: CharacterProfile, compatibility: str
    ) -> List[str]:
        """Generate relationship suggestions.
        
        Args:
            profile1: First profile
            profile2: Second profile
            compatibility: Compatibility assessment
            
        Returns:
            List of relationship suggestions
        """
        suggestions = []
        
        if compatibility == "conflict":
            suggestions.append("Potential rival or antagonist relationship")
            suggestions.append("Consider using their opposing values to create dramatic tension")
        
        elif compatibility == "high":
            suggestions.append("Strong potential for alliance or partnership")
            suggestions.append("Could work well as allies or team members")
            
            if profile1.role == "protagonist" and profile2.role == "protagonist":
                suggestions.append("Consider making them friends or companions")
        
        elif compatibility == "medium":
            suggestions.append("Neutral to positive relationship possible")
            suggestions.append("Could form temporary alliances based on shared goals")
            
            if profile1.species != profile2.species:
                suggestions.append("Cross-species relationship could add interesting dynamics")
        
        else:  # low
            suggestions.append("Relationship would require significant development")
            suggestions.append("Consider using them in separate storylines")
        
        # Add specific suggestions based on traits
        if profile1.occupation and profile2.occupation:
            if profile1.occupation != profile2.occupation:
                suggestions.append(f"Different occupations ({profile1.occupation} and {profile2.occupation}) could create complementary dynamics")
        
        return suggestions[:5]  # Limit to 5
    
    def _compare_with_llm(
        self, 
        first_profile: CharacterProfile, 
        second_profile: CharacterProfile,
        llm_engine: Any
    ) -> Optional[LLMAnalysis]:
        """Perform LLM-powered deep character comparison.
        
        Uses an LLM to provide nuanced analysis of character dynamics,
        story opportunities, and narrative potential.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            llm_engine: LLM engine instance
            
        Returns:
            LLMAnalysis with deep insights, or None if analysis fails
        """
        try:
            from .prompting import build_similarity_prompt
            
            # Build prompt
            system_prompt, user_prompt = build_similarity_prompt(first_profile, second_profile)
            
            # Get LLM response
            response = llm_engine.generate(system_prompt, user_prompt)
            
            # Parse response (expecting structured format)
            analysis = self._parse_llm_response(response)
            
            return analysis
            
        except Exception as e:
            print(f"LLM comparison failed: {e}")
            return None
    
    def _parse_llm_response(self, response: str) -> Optional[LLMAnalysis]:
        """Parse LLM response into structured analysis.
        
        Args:
            response: LLM response text
            
        Returns:
            LLMAnalysis with parsed insights
        """
        # Try to parse JSON response
        try:
            data = json.loads(response)
            
            return LLMAnalysis(
                narrative_dynamics=data.get('narrative_dynamics', ''),
                story_opportunities=data.get('story_opportunities', []),
                scene_suggestions=data.get('scene_suggestions', []),
                dialogue_style=data.get('dialogue_style', ''),
                relationship_arc=data.get('relationship_arc', ''),
            )
        except json.JSONDecodeError:
            # Fall back to text parsing
            return LLMAnalysis(
                narrative_dynamics=response[:500],
                story_opportunities=[],
                scene_suggestions=[],
                dialogue_style='',
                relationship_arc='',
            )
    
    def _analyze_redundancy(
        self,
        first_profile: CharacterProfile,
        second_profile: CharacterProfile,
        overall_score: float
    ) -> MetaAnalysis:
        """Analyze character redundancy and rework potential.
        
        Detects when characters are too similar and provides suggestions
        for differentiation or merging.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            overall_score: Overall similarity score
            
        Returns:
            MetaAnalysis with redundancy assessment and suggestions
        """
        # Determine redundancy level
        if overall_score >= 0.95:
            redundancy_level = "extreme"
        elif overall_score >= 0.85:
            redundancy_level = "high"
        elif overall_score >= 0.75:
            redundancy_level = "medium"
        else:
            redundancy_level = "low"
        
        # Calculate uniqueness score (inverse of similarity)
        uniqueness_score = max(0.0, 1.0 - overall_score)
        
        # Detect issues
        issues = self._detect_redundancy_issues(first_profile, second_profile, overall_score)
        
        # Generate rework suggestions
        rework_suggestions1 = self._generate_rework_suggestions(first_profile, second_profile, "char1")
        rework_suggestions2 = self._generate_rework_suggestions(first_profile, second_profile, "char2")
        
        # Generate merge recommendation if extremely similar
        merge_recommendation = None
        if redundancy_level == "extreme":
            merge_recommendation = self._generate_merge_recommendation(first_profile, second_profile)
        
        return MetaAnalysis(
            redundancy_level=redundancy_level,
            redundancy_score=overall_score,
            issues_detected=issues,
            rework_suggestions_char1=rework_suggestions1,
            rework_suggestions_char2=rework_suggestions2,
            merge_recommendation=merge_recommendation,
            uniqueness_score=uniqueness_score,
        )
    
    def _detect_redundancy_issues(
        self,
        first_profile: CharacterProfile,
        second_profile: CharacterProfile,
        overall_score: float
    ) -> List[str]:
        """Detect specific redundancy issues between characters.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            overall_score: Overall similarity score
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # Check trait overlap
        trait_overlap = len(set(first_profile.personality_traits) & set(second_profile.personality_traits))
        total_traits = len(set(first_profile.personality_traits) | set(second_profile.personality_traits))
        
        if total_traits > 0 and trait_overlap / total_traits > 0.7:
            issues.append(f"Both share {trait_overlap}/{total_traits} personality traits")
        
        # Check value overlap
        value_overlap = len(set(first_profile.core_values) & set(second_profile.core_values))
        total_values = len(set(first_profile.core_values) | set(second_profile.core_values))
        
        if total_values > 0 and value_overlap / total_values > 0.7:
            issues.append(f"Both share {value_overlap}/{total_values} core values")
        
        # Check identical background elements
        if first_profile.species == second_profile.species and first_profile.species != "human":
            issues.append(f"Both are {first_profile.species}")
        
        if first_profile.occupation == second_profile.occupation and first_profile.occupation:
            issues.append(f"Both are {first_profile.occupation}")
        
        if first_profile.role == second_profile.role and first_profile.role != "unknown":
            issues.append(f"Both play {first_profile.role} roles")
        
        # Check goal overlap
        goal_overlap = len(set(first_profile.goals) & set(second_profile.goals))
        if goal_overlap > 0:
            issues.append(f"Share {goal_overlap} identical goals")
        
        return issues
    
    def _generate_rework_suggestions(
        self,
        first_profile: CharacterProfile,
        second_profile: CharacterProfile,
        target_character: str
    ) -> List[str]:
        """Generate rework suggestions to differentiate characters.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            target_character: Which character to generate suggestions for ("char1" or "char2")
            
        Returns:
            List of rework suggestions
        """
        if target_character == "char1":
            profile = first_profile
            other_profile = second_profile
            name = first_profile.name or "Character 1"
        else:
            profile = second_profile
            other_profile = first_profile
            name = second_profile.name or "Character 2"
        
        suggestions = []
        
        # Suggest trait changes
        shared_traits = set(profile.personality_traits) & set(other_profile.personality_traits)
        if shared_traits:
            trait_alternatives = {
                'brave': ['reckless', 'cautious', 'calculated'],
                'kind': ['pragmatic', 'ruthless', 'neutral'],
                'loyal': ['opportunistic', 'independent', 'flexible'],
                'honest': ['secretive', 'diplomatic', 'cunning'],
                'smart': ['wise', 'inventive', 'analytical'],
                'strong': ['agile', 'resilient', 'enduring'],
            }
            
            for trait in list(shared_traits)[:3]:
                if trait in trait_alternatives:
                    alternatives = [a for a in trait_alternatives[trait] if a not in other_profile.personality_traits]
                    if alternatives:
                        suggestions.append(f"Change '{trait}' to '{alternatives[0]}' - creates distinction")
        
        # Suggest value changes
        shared_values = set(profile.core_values) & set(other_profile.core_values)
        if shared_values:
            value_alternatives = {
                'justice': ['revenge', 'order', 'balance'],
                'mercy': ['honor', 'duty', 'survival'],
                'loyalty': ['ambition', 'freedom', 'independence'],
                'courage': ['wisdom', 'patience', 'strategy'],
            }
            
            for value in list(shared_values)[:2]:
                if value in value_alternatives:
                    alternatives = [a for a in value_alternatives[value] if a not in other_profile.core_values]
                    if alternatives:
                        suggestions.append(f"Shift '{value}' toward '{alternatives[0]}' - adds complexity")
        
        # Suggest motivation changes if they're the same
        shared_motivations = set(profile.motivations) & set(other_profile.motivations)
        if shared_motivations:
            suggestions.append(f"Differentiate motivation: currently share {len(shared_motivations)} motivations")
        
        # Suggest role changes if appropriate
        if profile.role == other_profile.role and profile.role not in ["unknown", "neutral"]:
            if profile.role == "protagonist":
                suggestions.append("Consider making this a supporting character instead")
            elif profile.role == "supporting":
                suggestions.append("Consider making this a protagonist with unique arc")
        
        # Suggest background changes
        if profile.occupation == other_profile.occupation and profile.occupation:
            suggestions.append(f"Change occupation from '{profile.occupation}' to something distinct")
        
        return suggestions[:5]
    
    def _generate_merge_recommendation(
        self,
        first_profile: CharacterProfile,
        second_profile: CharacterProfile
    ) -> str:
        """Generate recommendation for merging redundant characters.
        
        Args:
            first_profile: First character profile
            second_profile: Second character profile
            
        Returns:
            Merge recommendation text
        """
        # Determine which profile seems more developed
        first_development = len(first_profile.personality_traits) + len(first_profile.background_keywords)
        second_development = len(second_profile.personality_traits) + len(second_profile.background_keywords)
        
        primary = first_profile if first_development >= second_development else second_profile
        secondary = second_profile if first_development >= second_development else first_profile
        
        # Build recommendation
        parts = []
        
        parts.append(f"Merge into '{primary.name or 'Primary Character'}':")
        parts.append(f"• Keep {primary.name or 'Primary'}'s backstory (more developed)")
        
        # Identify best elements from secondary
        best_elements = []
        
        unique_secondary_traits = set(secondary.personality_traits) - set(primary.personality_traits)
        if unique_secondary_traits:
            best_elements.append(f"traits: {', '.join(list(unique_secondary_traits)[:3])}")
        
        unique_secondary_values = set(secondary.core_values) - set(primary.core_values)
        if unique_secondary_values:
            best_elements.append(f"values: {', '.join(list(unique_secondary_values)[:2])}")
        
        if best_elements:
            parts.append(f"• Add from {secondary.name or 'Secondary'}: {', '.join(best_elements)}")
        
        parts.append(f"• Result: Stronger, more unique character combining best of both")
        
        return '\n'.join(parts)


def format_similarity_report(result: SimilarityResult) -> str:
    """Format similarity result as readable report.
    
    Args:
        result: SimilarityResult to format
        
    Returns:
        Formatted report string
    """
    lines = []
    
    # Header
    lines.append(f"🔍 Similarity Analysis")
    lines.append(f"{'='*60}")
    lines.append(f"{result.character1_name} vs {result.character2_name}")
    lines.append("")
    
    # Overall score
    percentage = result.overall_score * 100
    bar_length = int(percentage / 10)
    bar = "█" * bar_length + "░" * (10 - bar_length)
    lines.append(f"Overall Similarity: {percentage:.1f}%")
    lines.append(f"[{bar}]")
    lines.append(f"Compatibility: {result.compatibility.upper()}")
    lines.append("")
    
    # Dimension scores
    lines.append("📊 Dimension Scores:")
    for dim, score in result.dimension_scores.items():
        dim_percentage = score * 100
        dim_bar = "█" * int(dim_percentage / 10) + "░" * (10 - int(dim_percentage / 10))
        lines.append(f"  {dim.capitalize()}: {dim_percentage:.1f}% [{dim_bar}]")
    lines.append("")
    
    # Conflict/Synergy
    lines.append(f"⚔️  Conflict Potential: {result.conflict_potential * 100:.1f}%")
    lines.append(f"🤝 Synergy Potential: {result.synergy_potential * 100:.1f}%")
    lines.append("")
    
    # Commonalities
    if result.commonalities:
        lines.append("✨ Commonalities:")
        for commonality in result.commonalities:
            lines.append(f"  • {commonality}")
        lines.append("")
    
    # Differences
    if result.differences:
        lines.append("⚡ Differences:")
        for difference in result.differences:
            lines.append(f"  • {difference}")
        lines.append("")
    
    # Relationship suggestions
    if result.relationship_suggestions:
        lines.append("💡 Relationship Suggestions:")
        for suggestion in result.relationship_suggestions:
            lines.append(f"  • {suggestion}")
        lines.append("")
    
    # LLM Analysis
    if result.llm_analysis:
        lines.append("🧠 LLM Deep Analysis")
        lines.append(f"{'─'*60}")
        
        if result.llm_analysis.narrative_dynamics:
            lines.append(f"\n📖 Narrative Dynamics:")
            lines.append(f"  {result.llm_analysis.narrative_dynamics}")
        
        if result.llm_analysis.story_opportunities:
            lines.append(f"\n🎬 Story Opportunities:")
            for opportunity in result.llm_analysis.story_opportunities:
                lines.append(f"  • {opportunity}")
        
        if result.llm_analysis.scene_suggestions:
            lines.append(f"\n🎭 Scene Suggestions:")
            for i, scene in enumerate(result.llm_analysis.scene_suggestions, 1):
                lines.append(f"  {i}. {scene}")
        
        if result.llm_analysis.dialogue_style:
            lines.append(f"\n💬 Dialogue Style:")
            lines.append(f"  {result.llm_analysis.dialogue_style}")
        
        if result.llm_analysis.relationship_arc:
            lines.append(f"\n📈 Relationship Arc:")
            lines.append(f"  {result.llm_analysis.relationship_arc}")
        
        lines.append("")
    
    # Meta Analysis
    if result.meta_analysis:
        lines.append("⚠️  META ANALYSIS: Character Redundancy")
        lines.append(f"{'─'*60}")
        
        # Redundancy score
        meta = result.meta_analysis
        redundancy_percentage = meta.redundancy_score * 100
        redundancy_bar = "█" * int(redundancy_percentage / 10) + "░" * (10 - int(redundancy_percentage / 10))
        lines.append(f"\n📊 Redundancy Score: {redundancy_percentage:.1f}% [{redundancy_bar}]")
        lines.append(f"Level: {meta.redundancy_level.upper()}")
        
        # Uniqueness score
        uniqueness_percentage = meta.uniqueness_score * 100
        uniqueness_bar = "█" * int(uniqueness_percentage / 10) + "░" * (10 - int(uniqueness_percentage / 10))
        lines.append(f"✨ Uniqueness Score: {uniqueness_percentage:.1f}% [{uniqueness_bar}]")
        
        # Issues detected
        if meta.issues_detected:
            lines.append(f"\n⚡ Issues Detected:")
            for issue in meta.issues_detected:
                lines.append(f"  • {issue}")
        
        # Rework suggestions for character 1
        if meta.rework_suggestions_char1:
            lines.append(f"\n🔧 Rework Suggestions for {result.character1_name}:")
            for suggestion in meta.rework_suggestions_char1:
                lines.append(f"  • {suggestion}")
        
        # Rework suggestions for character 2
        if meta.rework_suggestions_char2:
            lines.append(f"\n🔧 Rework Suggestions for {result.character2_name}:")
            for suggestion in meta.rework_suggestions_char2:
                lines.append(f"  • {suggestion}")
        
        # Merge recommendation
        if meta.merge_recommendation:
            lines.append(f"\n🔗 Merge Recommendation:")
            for line in meta.merge_recommendation.split('\n'):
                lines.append(f"  {line}")
        
        lines.append("")
    
    return '\n'.join(lines)
