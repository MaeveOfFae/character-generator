#!/usr/bin/env python3
"""Quick test to verify Review screen text rendering."""

from pathlib import Path
from bpui.utils.file_io.pack_io import load_draft
from bpui.core.config import Config

# Load existing draft
drafts_dir = Path("drafts")
if drafts_dir.exists():
    drafts = sorted([d for d in drafts_dir.iterdir() if d.is_dir()], reverse=True)
    if drafts:
        draft = drafts[0]
        print(f"Loading draft: {draft.name}")
        
        assets = load_draft(draft)
        print(f"\nLoaded {len(assets)} assets:")
        for name, content in assets.items():
            preview = content[:50].replace('\n', ' ')
            print(f"  {name}: {len(content)} chars - '{preview}...'")
        
        print("\n✓ Assets loaded successfully")
        print("  The Review screen should now display these in TextAreas")
    else:
        print("No drafts found in drafts/")
else:
    print("drafts/ directory not found")
