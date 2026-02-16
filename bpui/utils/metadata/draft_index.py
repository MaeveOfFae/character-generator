"""SQLite index for fast draft search and filtering."""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .metadata import DraftMetadata

logger = logging.getLogger(__name__)


class DraftIndex:
    """SQLite-backed index for draft metadata."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize draft index.
        
        Args:
            db_path: Path to SQLite database file (default: drafts/.index.db)
        """
        if db_path is None:
            db_path = Path.cwd() / "drafts" / ".index.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    path TEXT PRIMARY KEY,
                    character_name TEXT,
                    seed TEXT,
                    mode TEXT,
                    model TEXT,
                    genre TEXT,
                    created TEXT,
                    modified TEXT,
                    favorite INTEGER DEFAULT 0,
                    tags TEXT,
                    notes TEXT
                )
            """)
            
            # Create indexes for fast search
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_character_name 
                ON drafts(character_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created 
                ON drafts(created DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_favorite 
                ON drafts(favorite)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mode 
                ON drafts(mode)
            """)
            
            # Full-text search for seed and notes
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS drafts_fts 
                USING fts5(path, character_name, seed, tags, notes, content=drafts)
            """)
            
            # Triggers to keep FTS in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS drafts_fts_insert 
                AFTER INSERT ON drafts BEGIN
                    INSERT INTO drafts_fts(path, character_name, seed, tags, notes)
                    VALUES (new.path, new.character_name, new.seed, new.tags, new.notes);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS drafts_fts_update 
                AFTER UPDATE ON drafts BEGIN
                    UPDATE drafts_fts 
                    SET character_name = new.character_name,
                        seed = new.seed,
                        tags = new.tags,
                        notes = new.notes
                    WHERE path = new.path;
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS drafts_fts_delete 
                AFTER DELETE ON drafts BEGIN
                    DELETE FROM drafts_fts WHERE path = old.path;
                END
            """)
            
            conn.commit()
    
    def add_draft(self, draft_path: Path, metadata: DraftMetadata):
        """Add or update a draft in the index.
        
        Args:
            draft_path: Path to draft directory
            metadata: Draft metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO drafts 
                (path, character_name, seed, mode, model, genre, created, modified, 
                 favorite, tags, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(draft_path),
                metadata.character_name,
                metadata.seed,
                metadata.mode,
                metadata.model,
                metadata.genre,
                metadata.created,
                metadata.modified,
                1 if metadata.favorite else 0,
                ",".join(metadata.tags or []),
                metadata.notes
            ))
            conn.commit()
        
        logger.debug("Indexed draft: %s", draft_path)
    
    def remove_draft(self, draft_path: Path):
        """Remove a draft from the index.
        
        Args:
            draft_path: Path to draft directory
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM drafts WHERE path = ?", (str(draft_path),))
            conn.commit()
        
        logger.debug("Removed draft from index: %s", draft_path)
    
    def search(
        self,
        query: Optional[str] = None,
        mode: Optional[str] = None,
        favorite: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created",
        sort_desc: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Search drafts with filters.
        
        Args:
            query: Full-text search query (searches name, seed, tags, notes)
            mode: Filter by content mode (SFW/NSFW/Platform-Safe)
            favorite: Filter by favorite status
            tags: Filter by tags (any match)
            sort_by: Sort field (created, modified, character_name)
            sort_desc: Sort descending
            limit: Maximum results
        
        Returns:
            List of draft metadata dicts with 'path' key
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if query:
                # Full-text search
                sql = """
                    SELECT d.* FROM drafts d
                    JOIN drafts_fts fts ON d.path = fts.path
                    WHERE drafts_fts MATCH ?
                """
                params = [query]
            else:
                # Regular search
                sql = "SELECT * FROM drafts WHERE 1=1"
                params = []
            
            # Add filters
            if mode:
                sql += " AND mode = ?"
                params.append(mode)
            
            if favorite is not None:
                sql += " AND favorite = ?"
                params.append(str(1 if favorite else 0))
            
            if tags:
                # Match any tag
                tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
                sql += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in tags])
            
            # Sort
            sort_order = "DESC" if sort_desc else "ASC"
            sql += f" ORDER BY {sort_by} {sort_order}"
            
            # Limit
            if limit:
                sql += " LIMIT ?"
                params.append(str(limit))
            
            cursor = conn.execute(sql, params)
            results = []
            
            for row in cursor:
                results.append({
                    "path": row["path"],
                    "character_name": row["character_name"],
                    "seed": row["seed"],
                    "mode": row["mode"],
                    "model": row["model"],
                    "genre": row["genre"],
                    "created": row["created"],
                    "modified": row["modified"],
                    "favorite": bool(row["favorite"]),
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "notes": row["notes"]
                })
            
            return results
    
    def get_stats(self) -> Dict:
        """Get index statistics.
        
        Returns:
            Dict with total, by_mode, by_favorite counts
        """
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
            
            by_mode = {}
            for row in conn.execute("SELECT mode, COUNT(*) as count FROM drafts GROUP BY mode"):
                by_mode[row[0] or "unknown"] = row[1]
            
            favorites = conn.execute(
                "SELECT COUNT(*) FROM drafts WHERE favorite = 1"
            ).fetchone()[0]
            
            return {
                "total": total,
                "by_mode": by_mode,
                "favorites": favorites
            }
    
    def rebuild_index(self, drafts_root: Optional[Path] = None):
        """Rebuild index from all drafts on disk.
        
        Args:
            drafts_root: Root drafts directory (default: ./drafts)
        """
        if drafts_root is None:
            drafts_root = Path.cwd() / "drafts"
        
        if not drafts_root.exists():
            logger.warning("Drafts directory does not exist: %s", drafts_root)
            return
        
        # Clear existing index
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM drafts")
            conn.commit()
        
        logger.info("Rebuilding draft index from: %s", drafts_root)
        
        indexed = 0
        skipped = 0
        
        for draft_dir in drafts_root.iterdir():
            if not draft_dir.is_dir():
                continue
            
            metadata_path = draft_dir / ".metadata.json"
            if not metadata_path.exists():
                skipped += 1
                logger.debug("Skipping draft without metadata: %s", draft_dir)
                continue
            
            try:
                metadata = DraftMetadata.load(draft_dir)
                if metadata:
                    self.add_draft(draft_dir, metadata)
                    indexed += 1
                else:
                    skipped += 1
                    logger.debug("Skipping draft with no metadata: %s", draft_dir)
            except Exception as e:
                skipped += 1
                logger.error("Failed to index draft %s: %s", draft_dir, e)
        
        logger.info("Index rebuilt: %d indexed, %d skipped", indexed, skipped)
        
        return {"indexed": indexed, "skipped": skipped}
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags across all drafts.
        
        Returns:
            Sorted list of unique tags
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT tags FROM drafts WHERE tags != ''").fetchall()
            
            all_tags = set()
            for (tags_str,) in rows:
                if tags_str:
                    all_tags.update(tags_str.split(","))
            
            return sorted(all_tags)
