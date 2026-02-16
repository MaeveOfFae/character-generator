#!/usr/bin/env python3
"""Migrate existing drafts to include .metadata.json files."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bpui.metadata import DraftMetadata


def migrate_draft(draft_dir: Path) -> bool:
    """Migrate a single draft directory.
    
    Args:
        draft_dir: Path to draft directory
        
    Returns:
        True if migration successful or already migrated, False otherwise
    """
    metadata_path = draft_dir / ".metadata.json"
    
    # Skip if already has metadata
    if metadata_path.exists():
        print(f"  ✓ Already migrated: {draft_dir.name}")
        return True
    
    # Create default metadata
    try:
        metadata = DraftMetadata.create_default(draft_dir)
        metadata.save(draft_dir)
        print(f"  ✓ Migrated: {draft_dir.name}")
        print(f"     - Character: {metadata.character_name}")
        print(f"     - Seed: {metadata.seed} (default)")
        print(f"     - Created: {metadata.created}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to migrate {draft_dir.name}: {e}")
        return False


def main():
    """Main migration function."""
    # Find drafts directory
    repo_root = Path(__file__).parent.parent
    drafts_dir = repo_root / "drafts"
    
    if not drafts_dir.exists():
        print(f"No drafts directory found at {drafts_dir}")
        return 0
    
    # Find all draft directories
    draft_dirs = [d for d in drafts_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not draft_dirs:
        print("No draft directories found.")
        return 0
    
    print(f"Found {len(draft_dirs)} draft directories.")
    print("Migrating...\n")
    
    # Migrate each draft
    success_count = 0
    failure_count = 0
    
    for draft_dir in sorted(draft_dirs):
        if migrate_draft(draft_dir):
            success_count += 1
        else:
            failure_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"  ✓ Successful: {success_count}")
    if failure_count > 0:
        print(f"  ✗ Failed: {failure_count}")
    print(f"{'='*60}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
