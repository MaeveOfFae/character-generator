"""Prompt construction and blueprint loading."""

from pathlib import Path
from typing import Optional, List, Any
from bpui.utils.profiler import profile


def load_blueprint(name: str, repo_root: Optional[Path] = None) -> str:
    """Load a blueprint file from blueprints/ folder."""
    with profile("load_blueprint", blueprint=name):
        if repo_root is None:
            repo_root = Path.cwd()

        blueprint_path = repo_root / "blueprints" / f"{name}.md"
        if not blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint not found: {blueprint_path}")

        return blueprint_path.read_text(encoding='utf-8')


def load_rules(repo_root: Optional[Path] = None) -> List[str]:
    """Load all rule files from rules/ folder in order.
    
    Returns:
        List of rule file contents in filename order
    """
    if repo_root is None:
        repo_root = Path.cwd()

    rules_dir = repo_root / "rules"
    if not rules_dir.exists():
        return []

    # Get all .md files sorted by filename
    rule_files = sorted(rules_dir.glob("*.md"))
    
    rules = []
    for rule_file in rule_files:
        rules.append(rule_file.read_text(encoding='utf-8'))
    
    return rules


def get_rules_for_asset(asset_name: str, repo_root: Optional[Path] = None) -> str:
    """Get relevant rules for a specific asset.
    
    For individual assets, includes core rules that apply to all generation.
    
    Args:
        asset_name: Name of the asset (system_prompt, post_history, etc.)
        repo_root: Repository root path
        
    Returns:
        Combined rules as a single string
    """
    # Core rules that apply to all assets
    core_rule_files = [
        "00_scope_and_role.md",
        "09_adjustment_note_and_thin_seed.md",
        "20_user_agency_and_consent.md",
        "30_content_modes.md",
        "40_genre_and_tone.md",
        "50_anti_generic.md",
        "51_anti_moralizing_directive.md",
        "55_no_moral_sanitizing.md",
        "70_repo_hygiene.md",
    ]
    
    if repo_root is None:
        repo_root = Path.cwd()
    
    rules_dir = repo_root / "rules"
    if not rules_dir.exists():
        return ""
    
    rules = []
    for rule_file in core_rule_files:
        rule_path = rules_dir / rule_file
        if rule_path.exists():
            rules.append(rule_path.read_text(encoding='utf-8'))
    
    # Add asset-specific hard rules
    hard_rules_path = rules_dir / "60_blueprint_hard_rules.md"
    if hard_rules_path.exists():
        hard_rules = hard_rules_path.read_text(encoding='utf-8')
        # Extract only the section relevant to this asset
        section_pattern = rf"## {asset_name}\n+((?:[^#]|\n(?!## ))+)"
        import re
        match = re.search(section_pattern, hard_rules)
        if match:
            asset_rules = f"## {asset_name}\n{match.group(1)}"
            rules.append(asset_rules)
    
    return "\n\n---\n\n".join(rules)


def build_orchestrator_prompt(
    seed: str,
    mode: Optional[str] = None,
    repo_root: Optional[Path] = None,
    template=None
) -> tuple[str, str]:
    """Build orchestrator system + user prompts.

    Args:
        seed: The character seed
        mode: Content mode (SFW/NSFW/Platform-Safe) or None for auto
        repo_root: Repository root path
        template: Optional Template object for custom assets

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Load all rules
    rules = load_rules(repo_root)
    rules_text = "\n\n---\n\n".join(rules) if rules else ""
    
    # Load orchestrator blueprint
    orchestrator = load_blueprint("rpbotgenerator", repo_root)
    
    # If template provided, modify orchestrator to list custom assets
    if template:
        from .topological_sort import topological_sort
        try:
            asset_order = topological_sort(template.assets)
        except ValueError:
            asset_order = [asset.name for asset in template.assets] # fallback to unsorted
        
        asset_list = ", ".join(asset_order)
        template_override = f"\n\n## TEMPLATE OVERRIDE\n\nUsing custom template: {template.name}\n"
        template_override += f"Generate these assets in order: {asset_list}\n"
        template_override += "Follow the dependency order defined in the template.\n"
        orchestrator = orchestrator + template_override
    
    # Combine rules + blueprint for system prompt
    if rules_text:
        system_prompt = f"# RULES\n\n{rules_text}\n\n---\n\n# ORCHESTRATOR BLUEPRINT\n\n{orchestrator}"
    else:
        system_prompt = orchestrator

    # User prompt is simple: mode (if specified) + seed
    user_lines = []
    if mode:
        user_lines.append(f"Mode: {mode}")
    user_lines.append(f"SEED: {seed}")

    return system_prompt, "\n".join(user_lines)


def build_similarity_prompt(
    profile1: Any,
    profile2: Any
) -> tuple[str, str]:
    """Build LLM prompt for character similarity analysis.

    Args:
        profile1: First character profile (CharacterProfile)
        profile2: Second character profile (CharacterProfile)

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    
    system_prompt = """You are an expert character analyst specializing in understanding character relationships, dynamics, and narrative potential. Your task is to deeply analyze two characters and provide insights about how they would interact in a story.

You will receive structured character profiles containing:
- Basic information (name, age, gender, species, occupation)
- Personality traits
- Core values and beliefs
- Motivations and goals
- Fears and weaknesses
- Narrative role and power level

Your analysis should focus on:

1. **Narrative Dynamics**: How these characters would interact, the tension or harmony between them, and what makes their relationship interesting for readers.

2. **Story Opportunities**: Specific plot hooks, conflicts, or situations that would arise from their relationship.

3. **Scene Suggestions**: 2-3 specific scene ideas that would showcase their dynamic (setting, situation, what happens).

4. **Dialogue Style**: How they would talk to each other - conversational patterns, tone, verbal conflicts, etc.

5. **Relationship Arc**: How their relationship might evolve over a story - beginning, middle, and end states.

Provide your response as JSON with this structure:

```json
{
  "narrative_dynamics": "2-3 paragraphs describing the core dynamic",
  "story_opportunities": [
    "opportunity 1",
    "opportunity 2",
    "opportunity 3"
  ],
  "scene_suggestions": [
    "Scene 1 description with setting and action",
    "Scene 2 description with setting and action",
    "Scene 3 description with setting and action"
  ],
  "dialogue_style": "Description of their conversational patterns",
  "relationship_arc": "Description of how their relationship would develop"
}
```

Be specific, insightful, and focus on narrative potential. Consider:
- Would they clash or complement each other?
- What secrets or conflicts could emerge?
- How would they challenge each other to grow?
- What would readers find compelling about their relationship?
- What themes or conflicts would their relationship explore?"""

    # Build user prompt with character profiles
    user_lines = []
    
    # Character 1
    user_lines.append(f"## CHARACTER 1: {profile1.name or 'Character 1'}")
    user_lines.append(f"**Age**: {profile1.age or 'Unknown'}")
    user_lines.append(f"**Gender**: {profile1.gender or 'Unknown'}")
    user_lines.append(f"**Species**: {profile1.species or 'Unknown'}")
    user_lines.append(f"**Occupation**: {profile1.occupation or 'Unknown'}")
    user_lines.append(f"**Role**: {profile1.role or 'Unknown'}")
    user_lines.append(f"**Power Level**: {profile1.power_level or 'Unknown'}")
    user_lines.append(f"**Mode**: {profile1.mode or 'Unknown'}")
    
    if profile1.personality_traits:
        user_lines.append(f"**Personality Traits**: {', '.join(profile1.personality_traits[:10])}")
    
    if profile1.core_values:
        user_lines.append(f"**Core Values**: {', '.join(profile1.core_values[:10])}")
    
    if profile1.motivations:
        user_lines.append(f"**Motivations**: {', '.join(profile1.motivations[:10])}")
    
    if profile1.goals:
        user_lines.append(f"**Goals**: {', '.join(profile1.goals[:10])}")
    
    if profile1.fears:
        user_lines.append(f"**Fears**: {', '.join(profile1.fears[:10])}")
    
    # Character 2
    user_lines.append(f"\n## CHARACTER 2: {profile2.name or 'Character 2'}")
    user_lines.append(f"**Age**: {profile2.age or 'Unknown'}")
    user_lines.append(f"**Gender**: {profile2.gender or 'Unknown'}")
    user_lines.append(f"**Species**: {profile2.species or 'Unknown'}")
    user_lines.append(f"**Occupation**: {profile2.occupation or 'Unknown'}")
    user_lines.append(f"**Role**: {profile2.role or 'Unknown'}")
    user_lines.append(f"**Power Level**: {profile2.power_level or 'Unknown'}")
    user_lines.append(f"**Mode**: {profile2.mode or 'Unknown'}")
    
    if profile2.personality_traits:
        user_lines.append(f"**Personality Traits**: {', '.join(profile2.personality_traits[:10])}")
    
    if profile2.core_values:
        user_lines.append(f"**Core Values**: {', '.join(profile2.core_values[:10])}")
    
    if profile2.motivations:
        user_lines.append(f"**Motivations**: {', '.join(profile2.motivations[:10])}")
    
    if profile2.goals:
        user_lines.append(f"**Goals**: {', '.join(profile2.goals[:10])}")
    
    if profile2.fears:
        user_lines.append(f"**Fears**: {', '.join(profile2.fears[:10])}")
    
    user_lines.append("\n## TASK")
    user_lines.append("Provide a deep analysis of these two characters' relationship potential.")
    user_lines.append("Return your response as valid JSON following the structure specified in the system prompt.")
    
    return system_prompt, "\n".join(user_lines)


def build_asset_prompt(
    asset_name: str,
    seed: str,
    mode: Optional[str] = None,
    prior_assets: Optional[dict[str, str]] = None,
    repo_root: Optional[Path] = None,
    blueprint_content: Optional[str] = None,
) -> tuple[str, str]:
    """Build prompt for a single asset using its blueprint.

    Args:
        asset_name: Name of the asset (system_prompt, post_history, etc.)
        seed: The character seed
        mode: Content mode (SFW/NSFW/Platform-Safe) or None for auto
        prior_assets: Previously generated assets for context
        repo_root: Repository root path
        blueprint_content: Optional blueprint content to use instead of loading

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Load relevant rules for this asset
    rules = get_rules_for_asset(asset_name, repo_root)
    
    # Load asset blueprint
    if blueprint_content:
        blueprint = blueprint_content
    else:
        blueprint = load_blueprint(asset_name, repo_root)
    
    # Combine rules + blueprint for system prompt
    if rules:
        system_prompt = f"# RULES\n\n{rules}\n\n---\n\n# BLUEPRINT: {asset_name}\n\n{blueprint}"
    else:
        system_prompt = blueprint

    # Build user prompt with mode + seed + prior assets as context
    user_lines = []
    if mode:
        user_lines.append(f"Mode: {mode}")
    user_lines.append(f"SEED: {seed}")

    # Add prior assets as context (for hierarchy enforcement)
    if prior_assets:
        user_lines.append("\n---\n## Prior Assets (for context):\n")
        for prior_name, prior_content in prior_assets.items():
            user_lines.append(f"### {prior_name}:\n```\n{prior_content}\n```\n")

    return system_prompt, "\n".join(user_lines)


def build_seedgen_prompt(
    genre_lines: str,
    repo_root: Optional[Path] = None
) -> tuple[str, str]:
    """Build seed generator system + user prompts.

    Args:
        genre_lines: Multiline genre/theme input
        repo_root: Repository root path

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    seed_gen_path = (repo_root or Path.cwd()) / "tools" / "seed-gen.md"
    if not seed_gen_path.exists():
        raise FileNotFoundError(f"Seed generator not found: {seed_gen_path}")

    seed_gen = seed_gen_path.read_text(encoding='utf-8')
    return seed_gen, genre_lines


def build_refinement_chat_system(
    asset_name: str,
    current_content: str,
    character_sheet: str,
) -> str:
    """Build system prompt for chat-based asset refinement.

    Args:
        asset_name: Name of the asset being refined
        current_content: Current content of the asset
        character_sheet: Character sheet for context

    Returns:
        System prompt string
    """
    # Map asset names to friendly names and blueprint names
    asset_labels = {
        "system_prompt": "System Prompt",
        "post_history": "Post History",
        "character_sheet": "Character Sheet",
        "intro_scene": "Intro Scene",
        "intro_page": "Intro Page",
        "a1111": "A1111 Image Prompt",
        "suno": "Suno Music Prompt",
    }

    label = asset_labels.get(asset_name, asset_name)
    
    # Load the blueprint for this asset
    try:
        blueprint = load_blueprint(asset_name)
    except FileNotFoundError:
        blueprint = "(Blueprint not found)"

    prompt = f"""You are an expert assistant helping refine a character asset: **{label}**.

The user is working on a character generation project using the RPBotGenerator blueprint system. You have access to:
1. The blueprint specification for this asset
2. The current asset content
3. The character sheet (for maintaining consistency)

## Blueprint Specification for {label}:

```markdown
{blueprint}
```

## Current Asset: {label}

```
{current_content}
```

## Character Sheet (for context):

```
{character_sheet}
```

## Your Role:

- **Discuss**: Answer questions about the asset, explain choices, suggest improvements
- **Refine**: When requested, provide an edited version of the asset
- **Maintain Consistency**: Ensure edits align with the character sheet and blueprint requirements
- **Follow Blueprint**: Strictly adhere to the format, rules, and constraints specified in the blueprint above
- **Format**: When providing an edited version, output it in a single code block (```)

## Key Guidelines:

- **Never narrate {{{{user}}}} actions, thoughts, emotions, sensations, decisions, or consent**
- Preserve the asset's required format and structure exactly as specified in the blueprint
- Keep tone and voice consistent with the character's established personality
- Respect all "Hard Rules" and constraints from the blueprint
- Maintain token limits where specified
- For system_prompt and post_history: paragraph-only, ≤300 tokens, no headers/lists
- For character_sheet: maintain field order and structure exactly
- For intro_scene: second-person narrative, end with open loop
- For a1111/suno: follow the modular prompt format exactly (including [Control] blocks)

If the user asks for changes, provide the complete edited asset in a code block. Otherwise, discuss and advise.
"""

    return prompt


def build_offspring_prompt(
    parent1_assets: dict[str, str],
    parent2_assets: dict[str, str],
    parent1_name: str,
    parent2_name: str,
    mode: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> tuple[str, str]:
    """Build prompt for offspring generation from two parent characters.

    Args:
        parent1_assets: Dict of asset names to content for parent 1
        parent2_assets: Dict of asset names to content for parent 2
        parent1_name: Name of parent 1 (for reference)
        parent2_name: Name of parent 2 (for reference)
        mode: Content mode (SFW/NSFW/Platform-Safe) or None for auto
        repo_root: Repository root path

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Load the offspring generator blueprint
    blueprint = load_blueprint("offspring_generator", repo_root)
    
    # Use blueprint as system prompt
    system_prompt = blueprint
    
    # Build user prompt with parents' assets
    user_lines = []
    
    # Add mode if specified
    if mode:
        user_lines.append(f"Mode: {mode}")
    
    # Add parent 1's full character suite
    user_lines.append(f"\n## PARENT 1: {parent1_name}")
    user_lines.append("### System Prompt:\n```")
    user_lines.append(parent1_assets.get("system_prompt", ""))
    user_lines.append("```")
    user_lines.append("### Post History:\n```")
    user_lines.append(parent1_assets.get("post_history", ""))
    user_lines.append("```")
    user_lines.append("### Character Sheet:\n```")
    user_lines.append(parent1_assets.get("character_sheet", ""))
    user_lines.append("```")
    user_lines.append("### Intro Scene:\n```")
    user_lines.append(parent1_assets.get("intro_scene", ""))
    user_lines.append("```")
    
    # Add parent 2's full character suite
    user_lines.append(f"\n## PARENT 2: {parent2_name}")
    user_lines.append("### System Prompt:\n```")
    user_lines.append(parent2_assets.get("system_prompt", ""))
    user_lines.append("```")
    user_lines.append("### Post History:\n```")
    user_lines.append(parent2_assets.get("post_history", ""))
    user_lines.append("```")
    user_lines.append("### Character Sheet:\n```")
    user_lines.append(parent2_assets.get("character_sheet", ""))
    user_lines.append("```")
    user_lines.append("### Intro Scene:\n```")
    user_lines.append(parent2_assets.get("intro_scene", ""))
    user_lines.append("```")
    
    # Instruction
    user_lines.append("\n## INSTRUCTION:")
    user_lines.append("Analyze how these two parents would shape a new character's upbringing and generate the offspring's SEED.")
    
    return system_prompt, "\n".join(user_lines)

