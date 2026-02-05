# Draft Index System

## Overview

The Draft Index is a SQLite-backed system for fast search and filtering of character drafts. It's particularly useful for collections with >100 drafts where filesystem scanning becomes slow.

## Features

- **Fast Search**: Full-text search across character names, seeds, tags, and notes
- **Flexible Filtering**: Filter by content mode, favorite status, tags, and genre
- **Automatic Indexing**: Drafts are automatically indexed when created/modified
- **Sorted Results**: Sort by created date, modified date, or character name
- **Statistics**: Get counts by mode, favorites, total drafts

## Architecture

### Database Location

The index is stored at `drafts/.index.db` as a SQLite database.

### Schema

```sql
CREATE TABLE drafts (
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
);

-- Full-text search table (FTS5)
CREATE VIRTUAL TABLE drafts_fts USING fts5(
    path, character_name, seed, tags, notes, content=drafts
);
```

### Indexes

- `idx_character_name`: Fast character name lookups
- `idx_created`: Fast sorting by creation date
- `idx_favorite`: Fast favorite filtering
- `idx_mode`: Fast mode filtering
- Full-text search on: path, character_name, seed, tags, notes

## Usage

### CLI

#### Rebuild Index

```bash
# Rebuild from all drafts in ./drafts
python3 -m bpui.cli rebuild-index

# Rebuild from custom directory
python3 -m bpui.cli rebuild-index --drafts-dir /path/to/drafts
```

### GUI

1. Open **Settings** (⚙️)
2. Click **🔄 Rebuild Draft Index**
3. Wait for confirmation

### Programmatic

```python
from bpui.draft_index import DraftIndex
from pathlib import Path

# Create index
index = DraftIndex()

# Rebuild from disk
result = index.rebuild_index()
print(f"Indexed: {result['indexed']}, Skipped: {result['skipped']}")

# Search
results = index.search(
    query="detective",        # Full-text search
    mode="NSFW",              # Filter by mode
    favorite=True,            # Only favorites
    tags=["cyberpunk"],       # Filter by tags
    sort_by="created",        # Sort field
    sort_desc=True,           # Descending
    limit=10                  # Max results
)

# Get statistics
stats = index.get_stats()
print(f"Total: {stats['total']}")
print(f"Favorites: {stats['favorites']}")
print(f"By mode: {stats['by_mode']}")

# Get all tags
all_tags = index.get_all_tags()
```

## Automatic Indexing

The index is automatically maintained by `pack_io.py`:

- **Draft creation**: `create_draft_dir()` indexes new drafts
- **Draft modification**: `save_asset()` updates the index
- **Draft deletion**: `delete_draft()` removes from index

## Performance

### Without Index (Filesystem Scan)

- 10 drafts: ~10ms
- 100 drafts: ~100ms
- 1000 drafts: ~1000ms (1 second)
- 10000 drafts: ~10s

### With Index (SQLite Query)

- All collection sizes: ~5-10ms
- Full-text search: ~10-50ms (depending on result count)

## Troubleshooting

### Index Out of Sync

If you manually add/remove/modify drafts outside the GUI:

```bash
python3 -m bpui.cli rebuild-index
```

Or in GUI: **Settings** → **🔄 Rebuild Draft Index**

### Missing Drafts

Drafts without `.metadata.json` are skipped during indexing. Ensure all drafts have metadata.

### Search Not Finding Results

- Full-text search uses FTS5 tokenization (splits on whitespace/punctuation)
- Use partial words: "detect" matches "detective"
- Case-insensitive by default
- Try filtering without search query first to verify drafts are indexed

## Migration

Existing installations will automatically create the index on first use. Run `rebuild-index` to populate it:

```bash
python3 -m bpui.cli rebuild-index
```

## Technical Details

### FTS5 Configuration

- Default tokenizer: unicode61
- Supports prefix matching: `detect*`
- Phrase search: `"exact phrase"`
- Boolean operators: `detective OR noir`

### Triggers

The system uses SQLite triggers to keep the FTS table synchronized:

- `drafts_fts_insert`: Indexes new drafts
- `drafts_fts_update`: Updates existing drafts
- `drafts_fts_delete`: Removes deleted drafts

### Thread Safety

DraftIndex creates a new connection per operation, making it thread-safe for concurrent reads and writes.

## Future Enhancements

- [ ] Tag autocomplete from index
- [ ] Advanced search operators (AND, OR, NOT)
- [ ] Search history
- [ ] Saved searches/filters
- [ ] Export search results
