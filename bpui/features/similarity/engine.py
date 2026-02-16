"""Similarity analysis engine for character drafts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json
import re

from bpui.core.prompting import build_similarity_prompt
from bpui.utils.file_io.pack_io import load_draft


@dataclass
class CharacterProfile:
    """Structured character profile extracted from assets."""

    name: str = ""
    age: Optional[int] = None
    gender: str = ""
    species: str = "human"
    occupation: str = ""
    personality_traits: List[str] = field(default_factory=list)
    core_values: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    background_keywords: List[str] = field(default_factory=list)
    role: str = "unknown"
    power_level: str = "unknown"
    mode: str = "SFW"

    @classmethod
    def from_assets(cls, assets: Dict[str, str]) -> "CharacterProfile":
        """Extract profile fields from character assets."""
        sheet = (assets.get("character_sheet") or "").strip()
        text = "\n".join([sheet, assets.get("system_prompt", ""), assets.get("post_history", "")]).strip()

        profile = cls()
        if not text:
            return profile

        lines = [line.rstrip() for line in sheet.splitlines()]
        lower_text = text.lower()

        def _find_value(prefix: str) -> str:
            for line in lines:
                if line.lower().startswith(prefix.lower() + ":"):
                    return line.split(":", 1)[1].strip()
            return ""

        profile.name = _find_value("Name") or profile.name
        age_val = _find_value("Age")
        if age_val.isdigit():
            profile.age = int(age_val)
        profile.gender = _find_value("Gender") or profile.gender
        profile.species = (_find_value("Species") or profile.species).lower()
        profile.occupation = _find_value("Occupation") or profile.occupation

        def _collect_list(section: str) -> List[str]:
            items: List[str] = []
            in_section = False
            for line in lines:
                if re.match(rf"^{re.escape(section)}\s*:", line, flags=re.I):
                    in_section = True
                    remainder = line.split(":", 1)[1].strip()
                    if remainder:
                        items.extend([v.strip() for v in re.split(r",|;", remainder) if v.strip()])
                    continue
                if in_section:
                    if not line.strip():
                        break
                    if line.lstrip().startswith("-"):
                        items.append(line.lstrip()[1:].strip())
                    else:
                        items.extend([v.strip() for v in re.split(r",|;", line) if v.strip()])
            return items

        profile.personality_traits = _collect_list("Personality") or profile.personality_traits
        profile.core_values = _collect_list("Values") or _collect_list("Core Values") or profile.core_values
        profile.goals = _collect_list("Goals") or _collect_list("Motivation") or profile.goals
        profile.fears = _collect_list("Fears") or _collect_list("Weaknesses") or profile.fears

        # Background keywords: take key nouns from character_sheet if present
        for line in lines:
            if line.lower().startswith("background:"):
                remainder = line.split(":", 1)[1].strip()
                if remainder:
                    profile.background_keywords.extend([v.strip() for v in re.split(r",|;", remainder) if v.strip()])

        # Role detection
        if any(k in lower_text for k in ["protagonist", "hero", "main character"]):
            profile.role = "protagonist"
        elif any(k in lower_text for k in ["antagonist", "villain", "nemesis"]):
            profile.role = "antagonist"
        elif any(k in lower_text for k in ["supporting", "sidekick", "mentor", "companion"]):
            profile.role = "supporting"

        # Power level detection
        if any(k in lower_text for k in ["supreme", "deity", "god", "omnipotent", "ultimate power"]):
            profile.power_level = "high"
        elif any(k in lower_text for k in ["ordinary", "normal", "average", "no special", "mundane"]):
            profile.power_level = "low"

        # Mode detection
        if "nsfw" in lower_text:
            profile.mode = "NSFW"
        elif "platform-safe" in lower_text or "platform safe" in lower_text:
            profile.mode = "Platform-Safe"
        else:
            profile.mode = "SFW"

        return profile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "species": self.species,
            "occupation": self.occupation,
            "personality_traits": self.personality_traits,
            "core_values": self.core_values,
            "goals": self.goals,
            "fears": self.fears,
            "background_keywords": self.background_keywords,
            "role": self.role,
            "power_level": self.power_level,
            "mode": self.mode,
        }


@dataclass
class LLMAnalysis:
    narrative_dynamics: str = ""
    story_opportunities: List[str] = field(default_factory=list)
    scene_suggestions: List[str] = field(default_factory=list)
    dialogue_style: str = ""
    relationship_arc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative_dynamics": self.narrative_dynamics,
            "story_opportunities": self.story_opportunities,
            "scene_suggestions": self.scene_suggestions,
            "dialogue_style": self.dialogue_style,
            "relationship_arc": self.relationship_arc,
        }


@dataclass
class MetaAnalysis:
    redundancy_level: str = "low"
    redundancy_score: float = 0.0
    issues_detected: List[str] = field(default_factory=list)
    rework_suggestions_char1: List[str] = field(default_factory=list)
    rework_suggestions_char2: List[str] = field(default_factory=list)
    merge_recommendation: Optional[str] = None
    uniqueness_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "redundancy_level": self.redundancy_level,
            "redundancy_score": self.redundancy_score,
            "issues_detected": self.issues_detected,
            "rework_suggestions_char1": self.rework_suggestions_char1,
            "rework_suggestions_char2": self.rework_suggestions_char2,
            "merge_recommendation": self.merge_recommendation,
            "uniqueness_score": self.uniqueness_score,
        }


@dataclass
class SimilarityResult:
    character1_name: str
    character2_name: str
    overall_score: float
    compatibility: str = "medium"
    conflict_potential: float = 0.0
    synergy_potential: float = 0.0
    commonalities: List[str] = field(default_factory=list)
    differences: List[str] = field(default_factory=list)
    relationship_suggestions: List[str] = field(default_factory=list)
    llm_analysis: Optional[LLMAnalysis] = None
    meta_analysis: Optional[MetaAnalysis] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "character1_name": self.character1_name,
            "character2_name": self.character2_name,
            "overall_score": self.overall_score,
            "compatibility": self.compatibility,
            "conflict_potential": self.conflict_potential,
            "synergy_potential": self.synergy_potential,
            "commonalities": self.commonalities,
            "differences": self.differences,
            "relationship_suggestions": self.relationship_suggestions,
        }
        if self.llm_analysis:
            data["llm_analysis"] = self.llm_analysis.to_dict()
        if self.meta_analysis:
            data["meta_analysis"] = self.meta_analysis.to_dict()
        return data


class SimilarityAnalyzer:
    """Analyzer for comparing character profiles and drafts."""

    def _compare_lists(self, list1: List[str], list2: List[str]) -> float:
        set1 = {v.strip().lower() for v in list1 if v.strip()}
        set2 = {v.strip().lower() for v in list2 if v.strip()}
        if not set1 and not set2:
            return 0.0
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set1 | set2)

    def compare_profiles(
        self,
        profile1: CharacterProfile,
        profile2: CharacterProfile,
        use_llm: bool = False,
        llm_engine: Optional[Any] = None,
    ) -> SimilarityResult:
        traits_score = self._compare_lists(profile1.personality_traits, profile2.personality_traits)
        values_score = self._compare_lists(profile1.core_values, profile2.core_values)
        goals_score = self._compare_lists(profile1.goals, profile2.goals)
        background_score = self._compare_lists(profile1.background_keywords, profile2.background_keywords)

        scores = [traits_score, values_score, goals_score, background_score]
        overall = sum(scores) / len(scores)

        compatibility = self._assess_compatibility(profile1, profile2, overall)
        conflict = self._calculate_conflict_potential(profile1, profile2)
        synergy = self._calculate_synergy_potential(profile1, profile2)
        commonalities = self._find_commonalities(profile1, profile2)
        differences = self._find_differences(profile1, profile2)

        meta = self._analyze_redundancy(profile1, profile2, overall)
        llm_analysis = None
        if use_llm and llm_engine is not None:
            llm_analysis = self._run_llm_analysis(profile1, profile2, llm_engine)

        suggestions: List[str] = []
        if compatibility == "high":
            suggestions.append("Likely strong allies with shared goals.")
        elif compatibility == "medium":
            suggestions.append("Potential for cooperation with occasional friction.")
        elif compatibility == "low":
            suggestions.append("Could work together but need a unifying pressure.")
        else:
            suggestions.append("High conflict potential; strong antagonistic dynamic.")

        return SimilarityResult(
            character1_name=profile1.name or "Character 1",
            character2_name=profile2.name or "Character 2",
            overall_score=overall,
            compatibility=compatibility,
            conflict_potential=conflict,
            synergy_potential=synergy,
            commonalities=commonalities,
            differences=differences,
            relationship_suggestions=suggestions,
            llm_analysis=llm_analysis,
            meta_analysis=meta,
        )

    def compare_drafts(
        self,
        draft1: Path,
        draft2: Path,
        use_llm: bool = False,
        llm_engine: Optional[Any] = None,
    ) -> SimilarityResult:
        assets1 = load_draft(draft1)
        assets2 = load_draft(draft2)
        profile1 = CharacterProfile.from_assets(assets1)
        profile2 = CharacterProfile.from_assets(assets2)
        if not profile1.name:
            profile1.name = draft1.name
        if not profile2.name:
            profile2.name = draft2.name
        return self.compare_profiles(profile1, profile2, use_llm=use_llm, llm_engine=llm_engine)

    def compare_multiple(self, draft_dirs: List[Path]) -> Dict[Tuple[str, str], SimilarityResult]:
        results: Dict[Tuple[str, str], SimilarityResult] = {}
        for i in range(len(draft_dirs)):
            for j in range(i + 1, len(draft_dirs)):
                d1, d2 = draft_dirs[i], draft_dirs[j]
                result = self.compare_drafts(d1, d2)
                results[(d1.name, d2.name)] = result
        return results

    def cluster_characters(self, draft_dirs: List[Path], min_similarity: float = 0.6) -> List[List[str]]:
        names = [d.name for d in draft_dirs]
        parent = {name: name for name in names}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for i in range(len(draft_dirs)):
            for j in range(i + 1, len(draft_dirs)):
                d1, d2 = draft_dirs[i], draft_dirs[j]
                result = self.compare_drafts(d1, d2)
                if result.overall_score >= min_similarity:
                    union(d1.name, d2.name)

        clusters: Dict[str, List[str]] = {}
        for name in names:
            root = find(name)
            clusters.setdefault(root, []).append(name)

        return sorted(clusters.values(), key=len, reverse=True)

    def _find_commonalities(self, p1: CharacterProfile, p2: CharacterProfile) -> List[str]:
        common: List[str] = []
        if p1.species and p1.species == p2.species:
            common.append(f"Both are {p1.species}.")
        if p1.role != "unknown" and p1.role == p2.role:
            common.append(f"Both serve the role of {p1.role}.")
        if p1.occupation and p1.occupation.lower() == p2.occupation.lower():
            common.append(f"Both are {p1.occupation}.")

        shared_traits = set(t.lower() for t in p1.personality_traits) & set(t.lower() for t in p2.personality_traits)
        if shared_traits:
            common.append(f"Shared traits: {', '.join(sorted(shared_traits))}.")

        shared_values = set(v.lower() for v in p1.core_values) & set(v.lower() for v in p2.core_values)
        if shared_values:
            common.append(f"Shared values: {', '.join(sorted(shared_values))}.")

        shared_goals = set(g.lower() for g in p1.goals) & set(g.lower() for g in p2.goals)
        if shared_goals:
            common.append(f"Shared goals: {', '.join(sorted(shared_goals))}.")

        return common

    def _find_differences(self, p1: CharacterProfile, p2: CharacterProfile) -> List[str]:
        diffs: List[str] = []
        if p1.species and p2.species and p1.species != p2.species:
            diffs.append(f"Different species: {p1.species} vs {p2.species}.")
        if p1.role != "unknown" and p2.role != "unknown" and p1.role != p2.role:
            diffs.append(f"Different roles: {p1.role} vs {p2.role}.")
        if p1.power_level != "unknown" and p2.power_level != "unknown" and p1.power_level != p2.power_level:
            diffs.append(f"Different power levels: {p1.power_level} vs {p2.power_level}.")
        if p1.occupation and p2.occupation and p1.occupation.lower() != p2.occupation.lower():
            diffs.append(f"Different occupations: {p1.occupation} vs {p2.occupation}.")

        unique_traits_1 = set(t.lower() for t in p1.personality_traits) - set(t.lower() for t in p2.personality_traits)
        unique_traits_2 = set(t.lower() for t in p2.personality_traits) - set(t.lower() for t in p1.personality_traits)
        if unique_traits_1:
            diffs.append(f"Unique traits for {p1.name or 'char1'}: {', '.join(sorted(unique_traits_1))}.")
        if unique_traits_2:
            diffs.append(f"Unique traits for {p2.name or 'char2'}: {', '.join(sorted(unique_traits_2))}.")

        return diffs

    def _assess_compatibility(self, p1: CharacterProfile, p2: CharacterProfile, overall: float) -> str:
        if {p1.role, p2.role} == {"protagonist", "antagonist"} and overall < 0.5:
            return "conflict"
        if overall >= 0.75:
            return "high"
        if overall >= 0.5:
            return "medium"
        if overall >= 0.3:
            return "low"
        return "conflict"

    def _calculate_conflict_potential(self, p1: CharacterProfile, p2: CharacterProfile) -> float:
        conflict = 0.2
        if {p1.role, p2.role} == {"protagonist", "antagonist"}:
            conflict += 0.4
        values_overlap = self._compare_lists(p1.core_values, p2.core_values)
        conflict += max(0.0, 0.3 - values_overlap)
        return max(0.0, min(1.0, conflict))

    def _calculate_synergy_potential(self, p1: CharacterProfile, p2: CharacterProfile) -> float:
        synergy = 0.2
        goals_overlap = self._compare_lists(p1.goals, p2.goals)
        synergy += goals_overlap * 0.5
        if {p1.role, p2.role} == {"protagonist", "supporting"}:
            synergy += 0.2
        return max(0.0, min(1.0, synergy))

    def _detect_redundancy_issues(self, p1: CharacterProfile, p2: CharacterProfile, overall: float) -> List[str]:
        issues: List[str] = []
        shared_traits = set(t.lower() for t in p1.personality_traits) & set(t.lower() for t in p2.personality_traits)
        if len(shared_traits) >= 3:
            issues.append("High overlap in personality traits.")
        if p1.occupation and p1.occupation.lower() == p2.occupation.lower():
            issues.append(f"Both share the same occupation ({p1.occupation}).")
        shared_values = set(v.lower() for v in p1.core_values) & set(v.lower() for v in p2.core_values)
        if len(shared_values) >= 2:
            issues.append("Strong overlap in core values.")
        if p1.species == p2.species:
            issues.append("Same species background may reduce uniqueness.")
        if overall >= 0.9:
            issues.append("Overall similarity is very high.")
        return issues

    def _generate_rework_suggestions(self, p1: CharacterProfile, p2: CharacterProfile, target: str) -> List[str]:
        target_profile = p1 if target == "char1" else p2
        suggestions: List[str] = []

        alt_traits = {
            "brave": ["cautious", "reckless"],
            "kind": ["stern", "aloof"],
            "loyal": ["independent", "skeptical"],
            "smart": ["impulsive", "naive"],
        }

        shared_traits = set(t.lower() for t in p1.personality_traits) & set(t.lower() for t in p2.personality_traits)
        for trait in shared_traits:
            if trait in alt_traits:
                suggestions.append(f"Change '{trait}' to '{alt_traits[trait][0]}' or '{alt_traits[trait][1]}'.")

        if p1.occupation and p1.occupation.lower() == p2.occupation.lower():
            suggestions.append("Change occupation to avoid overlap.")
        if p1.species == p2.species:
            suggestions.append("Consider a different species or heritage.")

        if not suggestions:
            suggestions.append("Differentiate with unique goals or personal conflicts.")

        return suggestions

    def _generate_merge_recommendation(self, p1: CharacterProfile, p2: CharacterProfile) -> str:
        score1 = len(p1.personality_traits) + len(p1.core_values) + len(p1.background_keywords)
        score2 = len(p2.personality_traits) + len(p2.core_values) + len(p2.background_keywords)
        primary, secondary = (p1, p2) if score1 >= score2 else (p2, p1)

        unique_traits = set(secondary.personality_traits) - set(primary.personality_traits)
        unique_values = set(secondary.core_values) - set(primary.core_values)

        parts = [
            f"Consider merging; {primary.name or 'Character 1'} is more developed.",
        ]
        if unique_traits or unique_values:
            additions = []
            if unique_traits:
                additions.append(f"traits: {', '.join(sorted(unique_traits))}")
            if unique_values:
                additions.append(f"values: {', '.join(sorted(unique_values))}")
            parts.append(f"Include unique elements from {secondary.name or 'Character 2'} ({'; '.join(additions)}).")

        return " ".join(parts)

    def _analyze_redundancy(self, p1: CharacterProfile, p2: CharacterProfile, overall: float) -> MetaAnalysis:
        if overall >= 0.95:
            level = "extreme"
        elif overall >= 0.85:
            level = "high"
        elif overall >= 0.75:
            level = "medium"
        else:
            level = "low"

        issues = self._detect_redundancy_issues(p1, p2, overall)
        meta = MetaAnalysis(
            redundancy_level=level,
            redundancy_score=overall,
            issues_detected=issues,
            rework_suggestions_char1=self._generate_rework_suggestions(p1, p2, "char1"),
            rework_suggestions_char2=self._generate_rework_suggestions(p1, p2, "char2"),
            uniqueness_score=max(0.0, 1.0 - overall),
        )

        if level == "extreme":
            meta.merge_recommendation = self._generate_merge_recommendation(p1, p2)

        return meta

    def _parse_llm_response(self, response: str) -> LLMAnalysis:
        try:
            data = json.loads(response)
            return LLMAnalysis(
                narrative_dynamics=data.get("narrative_dynamics", ""),
                story_opportunities=data.get("story_opportunities", []) or [],
                scene_suggestions=data.get("scene_suggestions", []) or [],
                dialogue_style=data.get("dialogue_style", ""),
                relationship_arc=data.get("relationship_arc", ""),
            )
        except Exception:
            return LLMAnalysis(narrative_dynamics=response[:500])

    def _run_llm_analysis(self, p1: CharacterProfile, p2: CharacterProfile, llm_engine: Any) -> LLMAnalysis:
        system_prompt, user_prompt = build_similarity_prompt(p1, p2)
        output = llm_engine.generate(system_prompt, user_prompt)
        if hasattr(output, "__await__"):
            # If engine returns coroutine
            import asyncio
            output = asyncio.get_event_loop().run_until_complete(output)
        return self._parse_llm_response(str(output))


def format_similarity_report(result: SimilarityResult) -> str:
    lines = [
        f"{result.character1_name} vs {result.character2_name}",
        f"Similarity: {result.overall_score * 100:.1f}%",
        f"Compatibility: {result.compatibility}",
        f"Conflict Potential: {result.conflict_potential * 100:.1f}%",
        f"Synergy Potential: {result.synergy_potential * 100:.1f}%",
        "",
        "Commonalities:",
    ]
    if result.commonalities:
        lines.extend([f"  • {c}" for c in result.commonalities])
    else:
        lines.append("  • None")

    lines.append("\nDifferences:")
    if result.differences:
        lines.extend([f"  • {d}" for d in result.differences])
    else:
        lines.append("  • None")

    if result.llm_analysis:
        lines.append("\nLLM Analysis:")
        lines.append(f"  Dynamics: {result.llm_analysis.narrative_dynamics}")
        if result.llm_analysis.story_opportunities:
            lines.append("  Story Opportunities:")
            lines.extend([f"    - {s}" for s in result.llm_analysis.story_opportunities])
        if result.llm_analysis.scene_suggestions:
            lines.append("  Scene Suggestions:")
            lines.extend([f"    - {s}" for s in result.llm_analysis.scene_suggestions])
        if result.llm_analysis.dialogue_style:
            lines.append(f"  Dialogue Style: {result.llm_analysis.dialogue_style}")
        if result.llm_analysis.relationship_arc:
            lines.append(f"  Relationship Arc: {result.llm_analysis.relationship_arc}")

    if result.meta_analysis:
        lines.append("\nMeta Analysis:")
        lines.append(
            f"  Redundancy: {result.meta_analysis.redundancy_level} "
            f"({result.meta_analysis.redundancy_score * 100:.1f}%)"
        )
        if result.meta_analysis.issues_detected:
            lines.append("  Issues:")
            lines.extend([f"    - {i}" for i in result.meta_analysis.issues_detected])
        if result.meta_analysis.merge_recommendation:
            lines.append(f"  Merge: {result.meta_analysis.merge_recommendation}")

    return "\n".join(lines)
