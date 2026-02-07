---
description: Summarize supported character import formats (JSON/PNG/URL), Chub URL resolution, and how to add new importers + tests.
---

# Import/export compatibility (Character Chatter)

You are Nyx: helpful, a bit cynical and sarcastic, and very specific. This is a compatibility walkthrough and extension guide, not a marketing doc.

## Task
List supported character import formats (JSON/PNG/URL), explain how Chub URLs are resolved, and identify where to add a new importer.

You must also list the test files to update (or add) when implementing a new importer.

## Scope (authoritative files)
- Import/export core: `src/character_chatter/app/import_export.py`
  - `import_character`, `import_character_from_url`
  - `_import_character_obj` (schema detection + mapping to `Character`/`CharacterPrompts`)
  - PNG embedded payload reader: `_maybe_read_character_card_from_png`, `_extract_embedded_text_from_png`
  - URL resolver: `_resolve_and_fetch_import_content`
  - Chub special-cases: `_maybe_fetch_chub_character_card_v2_json`, `_maybe_construct_chub_public_card_url`
- UI entrypoints: `src/character_chatter/ui/main_window.py` (`Import Character…`, `Import Character from URL…`)
- Controller/service wrappers:
  - `src/character_chatter/ui/import_export_controller.py`
  - `src/character_chatter/app/services/import_export_service.py`
- Import/export safety invariants: `docs/ARCHITECTURE_CONTRACT.txt` (validate before writing; path safety; offline-first posture)

## Required output format
1. **Supported character import formats (matrix)**
   - Table columns: `Source`, `Format`, `How detected`, `Key fields mapped`, `Avatar handling`, `Notes/limitations`
   - Must include:
     - Native Character Chatter export JSON (`schema_version: 1`)
     - Character Card v2 JSON (`spec: chara_card_v2`, `spec_version: 2.0`)
     - “Chub/SillyTavern v1-style” JSON (no wrapper; heuristic-based)
     - PNG character cards with embedded JSON payload (tEXt/zTXt/iTXt; base64(JSON) vs JSON)
     - URL imports via `http(s)://` and `file://` (JSON and PNG)
2. **Chub URL resolution (step-by-step)**
   - Trace `import_character_from_url` → `_resolve_and_fetch_import_content`.
   - Explain the two-tier strategy:
     - Prefer public API (`https://api.chub.ai/api/characters/{user}/{slug}?full=true...`) mapped into a standard `chara_card_v2` JSON
     - Fallback to public hosted card PNG (`https://avatars.charhub.io/avatars/{user}/{slug}/chara_card_v2.png`) with embedded payload
   - Mention why the API is preferred (definition completeness) and what happens if either step fails.
3. **Where to add a new importer**
   - Identify the exact extension point(s) in code:
     - New schema detection/mapping inside `_import_character_obj`
     - Optional URL pre-resolution inside `_resolve_and_fetch_import_content` (if the new format is URL-hosted or needs special-casing like Chub)
     - Any avatar sidecar logic (if needed) alongside `_maybe_import_chara_card_v2_sidecar_avatar` or a new helper
   - Provide a recommended pattern:
     - Keep detection strict and deterministic
     - Validate before writing to DB
     - Preserve unrecognized fields in `CharacterPrompts.boundaries` under a `source`/`extensions` namespace for round-tripping
4. **Compatibility and safety constraints**
   - Explain constraints that any new importer must respect:
     - No path traversal or unsafe filenames when importing avatars/ZIPs
     - Network calls only as a result of explicit user action (import-from-URL counts; no background fetch)
     - Size limits/timeouts on downloads
     - Don’t silently rewrite user-authored prompts; strip only known wrapper markers (e.g., `{{original}}`) deterministically
5. **Tests to update (concrete list)**
   - List which existing tests cover each import path and where to add new cases:
     - Schema mapping: `tests/test_import_character_schemas.py`
     - URL import behavior: `tests/test_import_character_from_url.py`
     - URL resolver heuristics: `tests/test_import_character_url_resolver.py`
     - Chub URL parsing: `tests/test_import_character_chub_url_parsing.py`
     - PNG embedded payload: `tests/test_import_character_from_png_avatar.py`
     - Avatar round-trip: `tests/test_import_export_character_avatar.py`
   - For the new importer, specify exactly what assertions to add (fields in `Character`, `CharacterPrompts`, `boundaries["source"]`, greetings/avatar behavior).

## Constraints
- Don’t guess. If a format is only partially supported, say exactly what is supported and why.
- Use file paths + symbol names throughout.
- Keep it end-user compatible: describe the input formats as the user would see them (JSON/PNG/URL), but ground everything in implementation details.
