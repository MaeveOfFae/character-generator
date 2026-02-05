"""Asset version management for tracking edit history."""

import difflib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple


class AssetVersion:
    """Represents a versioned asset."""
    
    def __init__(self, asset_name: str, content: str, version: int, timestamp: str):
        self.asset_name = asset_name
        self.content = content
        self.version = version
        self.timestamp = timestamp


def get_versions_dir(draft_dir: Path) -> Path:
    """Get or create the versions directory for a draft."""
    versions_dir = draft_dir / ".versions"
    versions_dir.mkdir(exist_ok=True)
    return versions_dir


def get_version_path(draft_dir: Path, asset_name: str, version: int) -> Path:
    """Get the path for a specific version of an asset."""
    versions_dir = get_versions_dir(draft_dir)
    return versions_dir / f"{asset_name}.v{version}.txt"


def save_version(draft_dir: Path, asset_name: str, content: str) -> int:
    """
    Save a new version of an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset (e.g., 'character_sheet')
        content: Content to save
        
    Returns:
        Version number that was saved
    """
    # Get current version number
    current_version = get_latest_version_number(draft_dir, asset_name)
    new_version = current_version + 1
    
    # Save version
    version_path = get_version_path(draft_dir, asset_name, new_version)
    version_path.write_text(content, encoding="utf-8")
    
    # Save timestamp metadata
    timestamp_path = version_path.with_suffix(".timestamp")
    timestamp_path.write_text(datetime.now().isoformat(), encoding="utf-8")
    
    return new_version


def get_latest_version_number(draft_dir: Path, asset_name: str) -> int:
    """
    Get the latest version number for an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        
    Returns:
        Latest version number (0 if no versions exist)
    """
    versions_dir = get_versions_dir(draft_dir)
    
    versions = []
    for version_file in versions_dir.glob(f"{asset_name}.v*.txt"):
        try:
            # Extract version number from filename
            version_str = version_file.stem.split(".v")[1]
            versions.append(int(version_str))
        except (IndexError, ValueError):
            continue
    
    return max(versions) if versions else 0


def load_version(draft_dir: Path, asset_name: str, version: int) -> Optional[AssetVersion]:
    """
    Load a specific version of an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        version: Version number to load
        
    Returns:
        AssetVersion object or None if not found
    """
    version_path = get_version_path(draft_dir, asset_name, version)
    
    if not version_path.exists():
        return None
    
    content = version_path.read_text(encoding="utf-8")
    
    # Try to load timestamp
    timestamp_path = version_path.with_suffix(".timestamp")
    if timestamp_path.exists():
        timestamp = timestamp_path.read_text(encoding="utf-8")
    else:
        # Fallback to file modification time
        timestamp = datetime.fromtimestamp(version_path.stat().st_mtime).isoformat()
    
    return AssetVersion(asset_name, content, version, timestamp)


def list_versions(draft_dir: Path, asset_name: str) -> List[AssetVersion]:
    """
    List all versions of an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        
    Returns:
        List of AssetVersion objects, sorted newest first
    """
    versions = []
    latest_version = get_latest_version_number(draft_dir, asset_name)
    
    for version_num in range(1, latest_version + 1):
        version = load_version(draft_dir, asset_name, version_num)
        if version:
            versions.append(version)
    
    # Sort newest first
    versions.reverse()
    return versions


def get_diff(draft_dir: Path, asset_name: str, version1: int, version2: int) -> List[str]:
    """
    Get a unified diff between two versions.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        version1: First version number
        version2: Second version number
        
    Returns:
        List of diff lines
    """
    v1 = load_version(draft_dir, asset_name, version1)
    v2 = load_version(draft_dir, asset_name, version2)
    
    if not v1 or not v2:
        return []
    
    diff = difflib.unified_diff(
        v1.content.splitlines(keepends=True),
        v2.content.splitlines(keepends=True),
        fromfile=f"{asset_name} v{version1}",
        tofile=f"{asset_name} v{version2}",
        lineterm=""
    )
    
    return list(diff)


def get_diff_from_current(draft_dir: Path, asset_name: str, version: int, current_content: str) -> List[str]:
    """
    Get a diff between a version and the current content.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        version: Version number to compare with
        current_content: Current content
        
    Returns:
        List of diff lines
    """
    v = load_version(draft_dir, asset_name, version)
    
    if not v:
        return []
    
    diff = difflib.unified_diff(
        v.content.splitlines(keepends=True),
        current_content.splitlines(keepends=True),
        fromfile=f"{asset_name} v{version}",
        tofile=f"{asset_name} (current)",
        lineterm=""
    )
    
    return list(diff)


def rollback_to_version(draft_dir: Path, asset_name: str, version: int, asset_filename: str) -> bool:
    """
    Rollback an asset to a specific version.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        version: Version number to rollback to
        asset_filename: Filename of the asset (e.g., 'character_sheet.txt')
        
    Returns:
        True if successful, False otherwise
    """
    # Load the version
    v = load_version(draft_dir, asset_name, version)
    if not v:
        return False
    
    # Save current content as a new version before rollback
    asset_path = draft_dir / asset_filename
    if asset_path.exists():
        current_content = asset_path.read_text(encoding="utf-8")
        save_version(draft_dir, asset_name, current_content)
    
    # Write the old version as the current content
    asset_path.write_text(v.content, encoding="utf-8")
    
    return True


def prune_old_versions(draft_dir: Path, asset_name: str, keep_count: int = 10) -> int:
    """
    Prune old versions, keeping only the most recent N versions.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        keep_count: Number of recent versions to keep
        
    Returns:
        Number of versions deleted
    """
    versions = list_versions(draft_dir, asset_name)
    
    if len(versions) <= keep_count:
        return 0
    
    # Delete oldest versions
    versions_to_delete = versions[keep_count:]
    deleted_count = 0
    
    for version in versions_to_delete:
        version_path = get_version_path(draft_dir, asset_name, version.version)
        timestamp_path = version_path.with_suffix(".timestamp")
        
        try:
            version_path.unlink()
            if timestamp_path.exists():
                timestamp_path.unlink()
            deleted_count += 1
        except OSError:
            pass
    
    return deleted_count


def get_version_stats(draft_dir: Path, asset_name: str) -> dict:
    """
    Get statistics about versions for an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        
    Returns:
        Dict with version statistics
    """
    versions = list_versions(draft_dir, asset_name)
    
    if not versions:
        return {
            "total_versions": 0,
            "latest_version": 0,
            "oldest_timestamp": None,
            "newest_timestamp": None,
        }
    
    return {
        "total_versions": len(versions),
        "latest_version": versions[0].version,
        "oldest_timestamp": versions[-1].timestamp,
        "newest_timestamp": versions[0].timestamp,
    }


def delete_all_versions(draft_dir: Path, asset_name: str) -> int:
    """
    Delete all versions of an asset.
    
    Args:
        draft_dir: Path to the draft directory
        asset_name: Name of the asset
        
    Returns:
        Number of versions deleted
    """
    versions_dir = get_versions_dir(draft_dir)
    deleted_count = 0
    
    for version_file in versions_dir.glob(f"{asset_name}.v*.txt"):
        try:
            version_file.unlink()
            # Also delete timestamp if exists
            timestamp_file = version_file.with_suffix(".timestamp")
            if timestamp_file.exists():
                timestamp_file.unlink()
            deleted_count += 1
        except OSError:
            pass
    
    return deleted_count
