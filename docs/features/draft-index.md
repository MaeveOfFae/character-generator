# Draft Index

The draft index is a SQLite-backed search layer for local drafts. It keeps draft browsing fast even when `drafts/` grows large.

## Location

- database file: `drafts/.index.db`
- implementation: `bpui.utils.metadata.draft_index.DraftIndex`

## What It Indexes

- draft path
- character name
- seed
- mode
- model
- genre
- created / modified timestamps
- favorite flag
- tags
- notes

It also maintains an FTS5 table for searching names, seeds, tags, and notes.

## CLI Usage

```bash
# rebuild from the default drafts directory
bpui rebuild-index

# rebuild from a custom location
bpui rebuild-index --drafts-dir /path/to/drafts
```

## Programmatic Usage

```python
from bpui.utils.metadata.draft_index import DraftIndex

index = DraftIndex()
result = index.rebuild_index()

results = index.search(
    query="detective",
    mode="NSFW",
    favorite=True,
    tags=["cyberpunk"],
    sort_by="created",
    sort_desc=True,
    limit=10,
)

stats = index.get_stats()
```

## Automatic Updates

The index is maintained as drafts are created, modified, and deleted through the normal draft IO paths.

## Troubleshooting

### Index looks stale

Rebuild it manually:

```bash
bpui rebuild-index
```

### Drafts are missing

Drafts without valid `.metadata.json` may be skipped.

### Search is weaker than expected

FTS tokenization is whitespace/punctuation based. Prefix-style queries and partial keywords generally work better than very literal phrase expectations.
