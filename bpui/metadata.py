"""Draft metadata management."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List


@dataclass
class DraftMetadata:
    """Metadata for a character draft."""
    
    seed: str
    mode: Optional[str] = None  # SFW, NSFW, Platform-Safe, or None
    model: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    tags: Optional[List[str]] = None
    genre: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False
    character_name: Optional[str] = None
    
    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created is None:
            self.created = datetime.now().isoformat()
        if self.modified is None:
            self.modified = self.created
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "DraftMetadata":
        """Create from dictionary."""
        return cls(**data)
    
    def save(self, draft_dir: Path) -> None:
        """Save metadata to draft directory.
        
        Args:
            draft_dir: Path to draft directory
        """
        metadata_path = draft_dir / ".metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, draft_dir: Path) -> Optional["DraftMetadata"]:
        """Load metadata from draft directory.
        
        Args:
            draft_dir: Path to draft directory
            
        Returns:
            DraftMetadata instance or None if not found
        """
        metadata_path = draft_dir / ".metadata.json"
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path) as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None
    
    @classmethod
    def create_default(cls, draft_dir: Path) -> "DraftMetadata":
        """Create default metadata by inferring from directory.
        
        Args:
            draft_dir: Path to draft directory
            
        Returns:
            DraftMetadata with inferred values
        """
        # Try to infer character name from directory name
        dir_name = draft_dir.name
        # Format: YYYYMMDD_HHMMSS_character_name
        parts = dir_name.split("_", 2)
        character_name = parts[2] if len(parts) > 2 else "unknown"
        
        # Try to infer timestamps from files
        created = None
        modified = None
        
        # Check if any asset files exist
        for file_path in draft_dir.glob("*.txt"):
            if file_path.is_file():
                stat = file_path.stat()
                created_ts = datetime.fromtimestamp(stat.st_ctime).isoformat()
                modified_ts = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                if created is None or created_ts < created:
                    created = created_ts
                if modified is None or modified_ts > modified:
                    modified = modified_ts
        
        return cls(
            seed="unknown",
            mode=None,
            model=None,
            created=created,
            modified=modified,
            character_name=character_name
        )
    
    def update_modified(self) -> None:
        """Update modified timestamp to now."""
        self.modified = datetime.now().isoformat()


def migrate_draft_metadata(drafts_dir: Path) -> tuple[int, int]:
    """
    Migrate existing drafts to include metadata.
    
    Scans the drafts directory and creates default metadata for any
    drafts that don't already have it.
    
    Args:
        drafts_dir: Path to the drafts directory
        
    Returns:
        Tuple of (total_drafts, migrated_count)
    """
    if not drafts_dir.exists():
        return (0, 0)
    
    total = 0
    migrated = 0
    
    for draft_path in drafts_dir.iterdir():
        if not draft_path.is_dir():
            continue
        
        # Skip hidden directories
        if draft_path.name.startswith("."):
            continue
        
        total += 1
        
        # Check if metadata already exists
        if (draft_path / ".metadata.json").exists():
            continue
        
        # Create default metadata
        metadata = DraftMetadata.create_default(draft_path)
        try:
            metadata.save(draft_path)
            migrated += 1
        except OSError:
            pass
    
    return (total, migrated)


def search_metadata(
    drafts_dir: Path,
    query: str = "",
    tags: list[str] | None = None,
    genre: str = "",
    favorite_only: bool = False
) -> list[tuple[Path, DraftMetadata]]:
    """
    Search drafts by metadata.
    
    Args:
        drafts_dir: Path to the drafts directory
        query: Search query (matches name, character name, or notes)
        tags: List of tags to filter by (any match)
        genre: Genre to filter by
        favorite_only: Only return favorites
        
    Returns:
        List of (draft_path, metadata) tuples matching the criteria
    """
    if not drafts_dir.exists():
        return []
    
    results = []
    query_lower = query.lower()
    tags_lower = [t.lower() for t in (tags or [])]
    genre_lower = genre.lower()
    
    for draft_path in drafts_dir.iterdir():
        if not draft_path.is_dir() or draft_path.name.startswith("."):
            continue
        
        metadata = DraftMetadata.load(draft_path)
        if not metadata:
            # Create default metadata for drafts without it
            metadata = DraftMetadata.create_default(draft_path)
        
        # Apply filters
        if query_lower:
            name_match = query_lower in draft_path.name.lower()
            char_match = metadata.character_name and query_lower in metadata.character_name.lower()
            notes_match = metadata.notes and query_lower in metadata.notes.lower()
            seed_match = query_lower in metadata.seed.lower()
            if not (name_match or char_match or notes_match or seed_match):
                continue
        
        if tags_lower and metadata.tags:
            meta_tags_lower = [t.lower() for t in metadata.tags]
            if not any(tag in meta_tags_lower for tag in tags_lower):
                continue
        
        if genre_lower and (not metadata.genre or genre_lower not in metadata.genre.lower()):
            continue
        
        if favorite_only and not metadata.favorite:
            continue
        
        results.append((draft_path, metadata))
    
    return results


def get_all_tags(drafts_dir: Path) -> list[str]:
    """
    Get all unique tags from all drafts.
    
    Args:
        drafts_dir: Path to the drafts directory
        
    Returns:
        Sorted list of unique tags
    """
    if not drafts_dir.exists():
        return []
    
    all_tags = set()
    
    for draft_path in drafts_dir.iterdir():
        if not draft_path.is_dir() or draft_path.name.startswith("."):
            continue
        
        metadata = DraftMetadata.load(draft_path)
        if metadata and metadata.tags:
            all_tags.update(metadata.tags)
    
    return sorted(all_tags)


def get_all_genres(drafts_dir: Path) -> list[str]:
    """
    Get all unique genres from all drafts.
    
    Args:
        drafts_dir: Path to the drafts directory
        
    Returns:
        Sorted list of unique genres (excluding empty strings)
    """
    if not drafts_dir.exists():
        return []
    
    all_genres = set()
    
    for draft_path in drafts_dir.iterdir():
        if not draft_path.is_dir() or draft_path.name.startswith("."):
            continue
        
        metadata = DraftMetadata.load(draft_path)
        if metadata and metadata.genre:
            all_genres.add(metadata.genre)
    
    return sorted(all_genres)
