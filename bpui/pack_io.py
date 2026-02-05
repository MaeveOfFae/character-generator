"""Pack I/O: draft directory management."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .parse_blocks import ASSET_FILENAMES
from .metadata import DraftMetadata


def create_draft_dir(
    assets: Dict[str, str],
    character_name: str,
    drafts_root: Optional[Path] = None,
    seed: Optional[str] = None,
    mode: Optional[str] = None,
    model: Optional[str] = None
) -> Path:
    """Create a draft directory with assets.

    Args:
        assets: Dict mapping asset names to content
        character_name: Sanitized character name
        drafts_root: Root drafts directory
        seed: Original character seed
        mode: Content mode (SFW/NSFW/Platform-Safe)
        model: LLM model used

    Returns:
        Path to created draft directory
    """
    if drafts_root is None:
        drafts_root = Path.cwd() / "drafts"

    drafts_root.mkdir(exist_ok=True)

    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_dir = drafts_root / f"{timestamp}_{character_name}"
    draft_dir.mkdir(parents=True, exist_ok=True)

    # Write each asset
    for asset_name, content in assets.items():
        filename = ASSET_FILENAMES.get(asset_name)
        if filename:
            (draft_dir / filename).write_text(content)

    # Create and save metadata
    metadata = DraftMetadata(
        seed=seed or "unknown",
        mode=mode,
        model=model,
        character_name=character_name
    )
    metadata.save(draft_dir)

    return draft_dir


def list_drafts(drafts_root: Optional[Path] = None) -> List[Path]:
    """List all draft directories.

    Args:
        drafts_root: Root drafts directory

    Returns:
        List of draft directory paths (sorted newest first)
    """
    if drafts_root is None:
        drafts_root = Path.cwd() / "drafts"

    if not drafts_root.exists():
        return []

    drafts = [d for d in drafts_root.iterdir() if d.is_dir()]
    drafts.sort(reverse=True)  # Newest first
    return drafts


def load_draft(draft_dir: Path) -> Dict[str, str]:
    """Load assets from a draft directory.

    Args:
        draft_dir: Draft directory path

    Returns:
        Dict mapping asset names to content
    """
    assets = {}
    for asset_name, filename in ASSET_FILENAMES.items():
        file_path = draft_dir / filename
        if file_path.exists():
            assets[asset_name] = file_path.read_text()
    return assets


def delete_draft(draft_dir: Path) -> None:
    """Delete a draft directory.

    Args:
        draft_dir: Draft directory path
    """
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
