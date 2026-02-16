# Similarity Analyzer Enhancements

## Summary

This document describes the enhancements made to the character similarity analyzer, including LLM-powered deep analysis and comprehensive meta/redundancy analysis features.

---

## New Features

### 1. LLM-Powered Deep Analysis

**Purpose:** Provide nuanced, narrative-focused insights into character relationships beyond simple trait comparison.

**Components:**
- `LLMAnalysis` dataclass in `bpui/similarity.py`
- `build_similarity_prompt()` function in `bpui/prompting.py`
- `_compare_with_llm()` method in `SimilarityAnalyzer` class

**Outputs:**
- **Narrative Dynamics**: How characters interact, tension/harmony, story interest
- **Story Opportunities**: Specific plot hooks, conflicts, situations
- **Scene Suggestions**: 2-3 specific scene ideas with setting and action
- **Dialogue Style**: Conversational patterns, tone, verbal conflicts
- **Relationship Arc**: Beginning, middle, and end states of relationship development

**Integration:**
- **CLI**: `--use-llm` flag in `bpui similarity` command
- **TUI**: Checkbox in Similarity screen
- **GUI**: Checkbox in Similarity widget

---

### 2. Meta/Redundancy Analysis

**Purpose:** Detect when characters are too similar and provide actionable rework or merge suggestions.

**Components:**
- `MetaAnalysis` dataclass in `bpui/similarity.py`
- `_analyze_redundancy()` method in `SimilarityAnalyzer` class
- `_detect_redundancy_issues()` - Identifies specific overlapping traits
- `_generate_rework_suggestions()` - Creates differentiation ideas
- `_generate_merge_recommendation()` - Suggests merging extreme duplicates

**Redundancy Levels:**
| Level | Score | Action |
|--------|--------|--------|
| **Low** | <75% | No action needed |
| **Medium** | 75-85% | Optional differentiation |
| **High** | 85-95% | Recommended rework |
| **Extreme** | >95% | Consider merging |

**Outputs:**
- **Redundancy Score**: 0-100% similarity rating
- **Issues Detected**: Specific overlapping traits, values, occupations
- **Rework Suggestions**: Character-specific differentiation ideas
  - Alternative personality traits
  - Shifted core values
  - Different motivations
  - Role changes
- **Merge Recommendation**: (Extreme only) Actionable merge plan
- **Uniqueness Score**: How distinct characters are (inverse of similarity)

**Example Rework Suggestions:**
```
For Character A (Warrior):
• Change 'brave' to 'reckless' - creates interesting flaw
• Add 'strategic thinker' - contrasts with Character B
• Shift motivation from 'protect village' to 'avenge family'
• Consider making them older, more experienced

For Character B (Knight):
• Change 'loyal' to 'opportunist' - adds moral ambiguity
• Add 'secretive' - contrasts with Character A's openness
• Shift from 'protect' to 'manipulate' as motivation
• Different occupation (scholar, merchant, etc.)
```

**Example Merge Recommendation:**
```
Merge into 'Primary Character':
• Keep Primary's backstory (more developed)
• Add from Secondary: traits: cunning, values: loyalty
• Result: Stronger, more unique character combining best of both
```

---

## Updated Report Format

The similarity report now includes two new sections:

### 🧠 LLM Deep Analysis Section
```
🧠 LLM Deep Analysis
────────────────────────────────────────────────────────────────────

📖 Narrative Dynamics:
  [Detailed analysis of character interaction patterns]

🎬 Story Opportunities:
  • [Specific plot hooks]
  • [Conflicts that could arise]
  • [Narrative opportunities]

🎭 Scene Suggestions:
  1. [Scene 1: setting, situation, action]
  2. [Scene 2: setting, situation, action]
  3. [Scene 3: setting, situation, action]

💬 Dialogue Style:
  [Description of conversational patterns]

📈 Relationship Arc:
  [How relationship would develop over story]
```

### ⚠️ META ANALYSIS Section
```
⚠️  META ANALYSIS: Character Redundancy
────────────────────────────────────────────────────────────────────

📊 Redundancy Score: 87% [█████████░]
Level: HIGH

✨ Uniqueness Score: 13% [█░░░░░░░░]

⚡ Issues Detected:
  • Both share 12/15 personality traits
  • Both share 8/10 core values
  • Both are warriors

🔧 Rework Suggestions for Character 1:
  • Change 'brave' to 'reckless' - creates distinction
  • Add 'strategic thinker' - contrasts with Character 2
  • Shift motivation to 'avenge family'

🔧 Rework Suggestions for Character 2:
  • Change 'loyal' to 'opportunist' - adds moral ambiguity
  • Different occupation from 'warrior'

🔗 Merge Recommendation:
  (Only for Extreme redundancy >95%)
  • Detailed merge plan with primary/secondary selection
  • List of unique elements to preserve
```

---

## Data Structures

### LLMAnalysis
```python
@dataclass
class LLMAnalysis:
    narrative_dynamics: str = ""
    story_opportunities: List[str] = []
    scene_suggestions: List[str] = []
    dialogue_style: str = ""
    relationship_arc: str = ""
```

### MetaAnalysis
```python
@dataclass
class MetaAnalysis:
    redundancy_level: str = "low"  # low, medium, high, extreme
    redundancy_score: float = 0.0  # 0-1
    issues_detected: List[str] = []
    rework_suggestions_char1: List[str] = []
    rework_suggestions_char2: List[str] = []
    merge_recommendation: Optional[str] = None
    uniqueness_score: float = 1.0  # 0-1
```

### SimilarityResult (Updated)
```python
@dataclass
class SimilarityResult:
    # ... existing fields ...
    llm_analysis: Optional[LLMAnalysis] = None
    meta_analysis: Optional[MetaAnalysis] = None
```

---

## Usage Examples

### CLI with LLM Analysis
```bash
# Basic comparison
bpui similarity character1 character2 --use-llm

# All pairs with LLM analysis
bpui similarity drafts --all --use-llm

# JSON output with LLM analysis
bpui similarity char1 char2 --use-llm --format json
```

### TUI
1. Navigate to Similarity screen
2. Select two characters
3. Check "Enable LLM Deep Analysis"
4. Press "Compare Characters"
5. View full report with both analyses

### GUI
1. Open Similarity widget
2. Select two characters
3. Check "Enable LLM Deep Analysis"
4. Click "Compare Characters"
5. View formatted report

---

## Testing

Comprehensive test suite added in `tests/unit/test_similarity_enhanced.py`:

- **27 tests** covering:
  - LLMAnalysis dataclass (3 tests)
  - MetaAnalysis dataclass (3 tests)
  - SimilarityResult with enhanced fields (3 tests)
  - Redundancy detection logic (3 tests)
  - Rework suggestion generation (2 tests)
  - Merge recommendation generation (2 tests)
  - Full redundancy analysis (4 tests)
  - LLM comparison and parsing (3 tests)
  - CharacterProfile extraction (4 tests)

**Test Results:** ✅ All 27 tests passing

---

## Implementation Details

### LLM Prompt Template
The `build_similarity_prompt()` function creates a sophisticated prompt that:
- Explains the analysis goal to the LLM
- Structures character profiles for easy reference
- Defines expected JSON output format
- Guides LLM to focus on narrative potential, story opportunities, and relationship arcs

### Redundancy Detection Logic
The redundancy analyzer:
- Calculates overlap percentages for traits, values, goals
- Detects identical background elements (species, occupation, role)
- Identifies shared motivations
- Generates specific, actionable suggestions
- Prioritizes "best of both" when recommending merges

### Rework Suggestion Algorithm
1. Identify shared traits between characters
2. Look up alternative traits that:
   - Are semantically related but different
   - Aren't already used by the other character
3. Suggest specific changes that:
   - Create contrast between characters
   - Add complexity or flaws
   - Maintain character viability

---

## Future Enhancements

Potential future improvements:
- **Auto-Rework Assistant**: One-click generate 3 distinct variants
- **Project-Wide Analysis**: "Find All Similar Pairs" batch mode
- **Visual Clustering**: Dendrogram or force-directed graph visualization
- **Trait Conflict Detection**: Identify contradictory trait combinations
- **Narrative Arc Generator**: Auto-generate story outlines based on character relationships

---

## Files Modified

### Core Logic
- `bpui/similarity.py` - Added LLM and meta analysis methods
- `bpui/prompting.py` - Added `build_similarity_prompt()` function

### User Interfaces
- `bpui/gui/similarity.py` - Added LLM checkbox option
- `bpui/tui/similarity.py` - Added LLM checkbox option
- `bpui/cli.py` - Added `--use-llm` flag

### Tests
- `tests/unit/test_similarity_enhanced.py` - New comprehensive test suite

---

## Conclusion

These enhancements transform the similarity analyzer from a basic trait comparison tool into a sophisticated character development aid that:

✅ Provides **narrative insights** via LLM analysis
✅ Detects **character redundancy** across projects
✅ Offers **actionable rework suggestions**
✅ Recommends **merges** for extreme duplicates
✅ Helps **improve character diversity**
✅ Maintains **backward compatibility** (all features optional)

The meta analysis in particular helps writers and character designers identify when their cast has too many similar characters and provides concrete steps to make each character more unique and compelling.