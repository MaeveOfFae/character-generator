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
