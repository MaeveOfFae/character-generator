"""Pack I/O: draft directory management."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from bpui.core.parse_blocks import ASSET_FILENAMES, get_asset_filename
from bpui.utils.metadata.metadata import DraftMetadata
from bpui.utils.metadata.draft_index import DraftIndex

if TYPE_CHECKING:
    from bpui.features.templates.templates import Template


def create_draft_dir(
    assets: Dict[str, str],
    character_name: str,
    drafts_root: Optional[Path] = None,
    seed: Optional[str] = None,
    mode: Optional[str] = None,
    model: Optional[str] = None,
    template: Optional['Template'] = None
) -> Path:
    """Create a draft directory with assets.

    Args:
        assets: Dict mapping asset names to content
        character_name: Sanitized character name
        drafts_root: Root drafts directory
        seed: Original character seed
        mode: Content mode (SFW/NSFW/Platform-Safe)
        model: LLM model used
        template: Optional template used for generation

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
        filename = get_asset_filename(asset_name, template)
        if filename:
            (draft_dir / filename).write_text(content)

    # Create and save metadata
    metadata = DraftMetadata(
        seed=seed or "unknown",
        mode=mode,
        model=model,
        character_name=character_name,
        template_name=template.name if template else None
    )
    metadata.save(draft_dir)
    
    # Add to index
    try:
        index = DraftIndex()
        index.add_draft(draft_dir, metadata)
    except Exception:
        pass  # Don't fail draft creation if indexing fails

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


def load_draft(draft_dir: Path, template: Optional['Template'] = None) -> Dict[str, str]:
    """Load assets from a draft directory.

    Args:
        draft_dir: Draft directory path
        template: Optional template defining asset filenames

    Returns:
        Dict mapping asset names to content
    """
    assets = {}
    
    if template:
        # Load assets based on template definition
        for asset_def in template.assets:
            filename = get_asset_filename(asset_def.name, template)
            file_path = draft_dir / filename
            if file_path.exists():
                assets[asset_def.name] = file_path.read_text()
    else:
        # Load default assets
        for asset_name, filename in ASSET_FILENAMES.items():
            file_path = draft_dir / filename
            if file_path.exists():
                assets[asset_name] = file_path.read_text()
    
    return assets


def save_draft(
    assets: Dict[str, str],
    seed: str,
    mode: Optional[str] = None,
    model: Optional[str] = None,
    template: Optional['Template'] = None
) -> Path:
    """Save assets as a new draft (convenience wrapper for create_draft_dir).
    
    Args:
        assets: Dict mapping asset names to content
        seed: Original character seed
        mode: Content mode (SFW/NSFW/Platform-Safe)
        model: LLM model used
        template: Optional template used for generation
    
    Returns:
        Path to created draft directory
    """
    # Extract character name from character_sheet
    char_sheet = assets.get("character_sheet", "")
    character_name = "character"
    
    for line in char_sheet.split("\n")[:10]:
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
            # Sanitize for filename
            character_name = "".join(c if c.isalnum() or c in "_ " else "_" for c in name.lower())
            character_name = "_".join(character_name.split())
            break
    
    return create_draft_dir(assets, character_name, seed=seed, mode=mode, model=model, template=template)


def delete_draft(draft_dir: Path) -> None:
    """Delete a draft directory.

    Args:
        draft_dir: Draft directory path
    """
    if draft_dir.exists():
        # Remove from index
        try:
            index = DraftIndex()
            index.remove_draft(draft_dir)
        except Exception:
            pass  # Don't fail deletion if index removal fails
        
        shutil.rmtree(draft_dir)


def save_asset(draft_dir: Path, asset_name: str, content: str, template: Optional['Template'] = None) -> None:
    """Save a single asset to a draft directory and update metadata.

    Args:
        draft_dir: Draft directory path
        asset_name: Name of the asset (e.g., 'character_sheet')
        content: Content to save
        template: Optional template defining asset filename
    """
    from .asset_versions import save_version
    
    filename = get_asset_filename(asset_name, template)
    if not filename:
        raise ValueError(f"Unknown asset name: {asset_name}")

    file_path = draft_dir / filename
    
    # Save version before overwriting (if file exists)
    if file_path.exists():
        old_content = file_path.read_text()
        save_version(draft_dir, asset_name, old_content)
    
    # Write new content
    file_path.write_text(content)

    # Update metadata modified timestamp
    metadata = DraftMetadata.load(draft_dir)
    if metadata:
        metadata.update_modified()
        metadata.save(draft_dir)
        
        # Update index
        try:
            index = DraftIndex()
            index.add_draft(draft_dir, metadata)
        except Exception:
            pass  # Don't fail save if indexing fails
