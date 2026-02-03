"""Prompt construction and blueprint loading."""

from pathlib import Path
from typing import Optional


def load_blueprint(name: str, repo_root: Optional[Path] = None) -> str:
    """Load a blueprint file from blueprints/ folder."""
    if repo_root is None:
        repo_root = Path.cwd()

    blueprint_path = repo_root / "blueprints" / f"{name}.md"
    if not blueprint_path.exists():
        raise FileNotFoundError(f"Blueprint not found: {blueprint_path}")

    return blueprint_path.read_text()


def build_orchestrator_prompt(
    seed: str,
    mode: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> tuple[str, str]:
    """Build orchestrator system + user prompts.

    Args:
        seed: The character seed
        mode: Content mode (SFW/NSFW/Platform-Safe) or None for auto
        repo_root: Repository root path

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    orchestrator = load_blueprint("rpbotgenerator", repo_root)

    # User prompt is simple: mode (if specified) + seed
    user_lines = []
    if mode:
        user_lines.append(f"Mode: {mode}")
    user_lines.append(f"SEED: {seed}")

    return orchestrator, "\n".join(user_lines)


def build_asset_prompt(
    asset_name: str,
    seed: str,
    mode: Optional[str] = None,
    prior_assets: Optional[dict[str, str]] = None,
    repo_root: Optional[Path] = None
) -> tuple[str, str]:
    """Build prompt for a single asset using its blueprint.

    Args:
        asset_name: Name of the asset (system_prompt, post_history, etc.)
        seed: The character seed
        mode: Content mode (SFW/NSFW/Platform-Safe) or None for auto
        prior_assets: Previously generated assets for context
        repo_root: Repository root path

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    blueprint = load_blueprint(asset_name, repo_root)

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

    return blueprint, "\n".join(user_lines)


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

    seed_gen = seed_gen_path.read_text()
    return seed_gen, genre_lines
