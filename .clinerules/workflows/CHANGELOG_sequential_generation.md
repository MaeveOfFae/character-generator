# Sequential Asset Generation - Implementation

**Date:** 2026-02-03  
**Change Type:** Architecture redesign  
**Impact:** High - changes core compilation behavior

## Summary

Changed character compilation from **single-shot** (one LLM call generating all 7 assets) to **sequential automated** (7 separate LLM calls, each generating one asset with prior assets as context).

## Motivation

1. **Better LLM Focus**: Each asset blueprint gets full attention instead of overwhelming the model with 7 simultaneous requirements
2. **Hierarchy Enforcement**: Later assets automatically receive prior assets as context, ensuring proper dependency handling
3. **Progress Visibility**: Users see each asset being generated in real-time
4. **Easier Debugging**: Failures isolated to specific assets instead of entire generation
5. **Format Compliance**: Individual blueprints easier to follow than complex orchestrator

## Changes Made

### 1. bpui/prompting.py

**Added `build_asset_prompt()` function:**

```python
def build_asset_prompt(
    asset_name: str,
    seed: str,
    mode: Optional[str] = None,
    prior_assets: Optional[dict[str, str]] = None,
    repo_root: Optional[Path] = None
) -> tuple[str, str]:
```

- Loads individual blueprint (e.g., `system_prompt.md`)
- Constructs user prompt with: mode, seed, prior assets as context
- Prior assets formatted as markdown sections for LLM reference

**Retained `build_orchestrator_prompt()` for backwards compatibility** (may be removed later)

### 2. bpui/parse_blocks.py

**Added `extract_single_asset()` function:**

```python
def extract_single_asset(output: str, asset_name: str) -> str:
```

- Extracts one codeblock from LLM output
- Handles optional Adjustment Note
- Returns asset content (text inside codeblock)

**Retained `parse_blueprint_output()` for backwards compatibility**

### 3. bpui/tui/compile.py

**Rewrote `compile_character()` method:**

**Before:**

1. Build orchestrator prompt with full rpbotgenerator.md
2. Single LLM call
3. Parse 7 codeblocks from output
4. Save draft

**After:**

1. Loop through `ASSET_ORDER` (system_prompt → post_history → ... → suno)
2. For each asset:
   - Build prompt with `build_asset_prompt(asset_name, seed, mode, prior_assets)`
   - Stream LLM output
   - Parse with `extract_single_asset(output, asset_name)`
   - Store in `assets` dict for next iteration
   - Show progress: `"→ Generating {asset_name}..."`
3. Extract character name from character_sheet once available
4. Save complete draft

**Benefits:**

- Real-time progress updates per asset
- Prior assets automatically included as context
- Better error isolation (shows which asset failed)
- Streaming output shows generation in progress

### 4. bpui/cli.py

**Updated `run_compile()` async function:**

- Same sequential logic as TUI
- Console output: `→ Generating system_prompt...` → `✓ system_prompt complete`
- Works with both `--out` (custom directory) and default (drafts/)

## Asset Order (Enforced)

```python
ASSET_ORDER = [
    "system_prompt",
    "post_history",
    "character_sheet",
    "intro_scene",
    "intro_page",
    "a1111",
    "suno",
]
```

Each asset receives all prior assets as context in the user prompt under `## Prior Assets (for context):` section.

## Context Injection Example

When generating `character_sheet` (3rd asset), the user prompt contains:

```markdown
Mode: NSFW
SEED: Cyberpunk hacker with memory implants

---
## Prior Assets (for context):

### system_prompt:

```
[content of system_prompt]
```

### post_history:

```
[content of post_history]
```

```

This ensures:

- Character sheet has access to behavioral rules (system_prompt)
- Character sheet knows current relationship state (post_history)
- No contradictions between assets
- Proper hierarchy enforcement

## Usage

**TUI:**

```bash
bpui
# Use Compile screen as before - now shows per-asset progress
```

**CLI:**

```bash
bpui compile --seed "Noir detective" --mode NSFW
# Now generates 7 assets sequentially with progress output
```

## Backwards Compatibility

- `build_orchestrator_prompt()` retained (unused)
- `parse_blueprint_output()` retained (unused)
- Old single-shot approach can be restored if needed
- All other screens (Review, Drafts, Settings) unchanged

## Testing Notes

1. **First Test**: Generate a simple seed to verify all 7 assets are generated
2. **Context Check**: Review later assets (e.g., intro_scene) to confirm they reference facts from earlier assets (e.g., character_sheet)
3. **Error Handling**: Interrupt generation mid-way to test cleanup
4. **Progress Display**: Verify TUI shows clear per-asset progress

## Future Enhancements

- [ ] Add "Regenerate Single Asset" button in Review screen
- [ ] Add "Continue from Failed Asset" recovery
- [ ] Consider removing unused orchestrator code after validation period
- [ ] Add option to toggle between sequential and single-shot modes
- [ ] Cache LLM engine between asset calls for efficiency

## Rollback Instructions

If issues occur:

1. Revert changes to `bpui/tui/compile.py` and `bpui/cli.py`
2. Change imports back to `build_orchestrator_prompt`, `parse_blueprint_output`
3. Use git history to restore original compile logic
4. `build_asset_prompt()` and `extract_single_asset()` can remain (no harm if unused)

## Related Files

- `.clinerules/workflows/generate-suite.md` - May need updating to reflect sequential approach
- `bpui/README.md` - Architecture section should be updated
- Test fixtures in `fixtures/` may need sequential output examples
