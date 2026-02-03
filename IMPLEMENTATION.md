# Blueprint UI Implementation Summary

## What Was Built

A complete terminal TUI application (`bpui`) that provides a portable, repo-local interface for the RPBotGenerator character compilation system.

## Core Features Delivered

### 1. Dual LLM Support ("Any LLM")

- **LiteLLM adapter**: Supports 100+ providers (OpenAI, Anthropic, Cohere, etc.) via unified API
- **OpenAI-compatible adapter**: Direct REST API calls for local models (Ollama, LM Studio, etc.)
- Both adapters support streaming for real-time output feedback

### 2. Terminal UI (Textual-based)

Six interactive screens:

- **Home**: Main menu with all actions
- **Settings**: Configure engine, model, API keys, test connections
- **Seed Generator**: Generate seed lists from genre/theme inputs
- **Compile**: Generate character suites from seeds with streaming output
- **Review**: Browse generated assets in tabs, validate, and export
- **Drafts**: Browse previously generated drafts
- **Validate**: Validate any directory against blueprint requirements

### 3. Strict Output Parser

- Extracts exactly 7 fenced codeblocks in required order
- Supports optional "Adjustment Note" first block
- Maps blocks to filenames per export contract
- Extracts character name from character_sheet for auto-naming

### 4. Draft Management

- Auto-saves to `drafts/<timestamp>_<sanitized_name>/`
- Browse, load, and re-validate/export drafts
- Preserves exact export contract filenames

### 5. Validation & Export Integration

- Wraps existing `tools/validate_pack.py` script
- Wraps existing `tools/export_character.sh` script
- Shows output in formatted log panels

### 6. CLI Companion

Subcommands for scripting:

- `bpui tui` - Launch TUI (default)
- `bpui compile` - Compile from seed
- `bpui seed-gen` - Generate seeds from file
- `bpui validate` - Validate directory
- `bpui export` - Export character

### 7. Configuration Management

- Repo-local `.bpui.toml` config file
- Settings: engine, model, api_key_env, base_url, temperature, max_tokens
- Gitignored by default

## File Structure Created

```
bpui/
  __init__.py
  config.py              # TOML config management
  llm/
    __init__.py
    base.py              # Abstract LLM interface
    litellm_engine.py    # LiteLLM adapter
    openai_compat_engine.py  # OpenAI-compatible adapter
  prompting.py           # Blueprint loading & prompt construction
  parse_blocks.py        # Strict 7-codeblock parser
  pack_io.py             # Draft directory management
  validate.py            # Validator wrapper
  export.py              # Export script wrapper
  tui/
    __init__.py
    app.py               # Main Textual app
    home.py              # Home screen
    settings.py          # Settings screen
    seed_generator.py    # Seed generator screen
    compile.py           # Compilation screen
    review.py            # Asset review screen
    drafts.py            # Draft browser
    validate_screen.py   # Validation screen
  cli.py                 # CLI entry point
  README.md              # Full documentation

pyproject.toml           # Package definition
test_bpui.py             # Installation test script
run_bpui.sh              # Convenience launcher
INSTALL.md               # Installation & quick start guide
.gitignore               # Updated with /drafts, .bpui.toml, etc.
```

## Key Design Decisions

### Parsing Strategy

- **Strict fenced-codeblock extraction**: Regex pattern `\`\`\`(?:[a-z]*\n)?(.*?)\`\`\``
- **7-block requirement**: System prompt, post history, character sheet, intro scene, intro page, A1111, Suno
- **Optional adjustment note**: First block matching `^Adjustment Note: .+$`
- **Character name extraction**: Parse `name: ...` from character_sheet, sanitize to `a-z0-9_`

### Architecture Patterns

- **Adapter pattern** for LLM engines (base interface + concrete implementations)
- **Async/await throughout** for streaming and non-blocking I/O
- **Composition over inheritance** in TUI screens (each screen is self-contained)
- **Config as dependency injection** (passed to screens, not global)

### UX Decisions

- **Content mode**: Auto by default (let orchestrator infer), with explicit override dropdown
- **Streaming preferred**: Real-time feedback during generation
- **Auto-validation**: Review screen validates on mount
- **Timestamped drafts**: Prevents name collisions, chronological sorting

### Error Handling

- All LLM calls wrapped in try/except with user-facing error messages
- Validation/export failures show stdout/stderr in formatted logs
- Connection test in Settings for diagnostic feedback

## Dependencies

### Core (required)

- `textual>=0.47.0` - TUI framework
- `rich>=13.7.0` - Rich text rendering
- `tomli-w>=1.0.0` - TOML writing
- `tomli>=2.0.1` - TOML reading (Python <3.11)
- `httpx>=0.26.0` - Async HTTP client

### Optional

- `litellm>=1.0.0` - Multi-provider LLM support (install with `pip install -e ".[litellm]"`)

## Installation Flow

1. User clones/downloads repo
2. Run `pip install -e .` (basic) or `pip install -e ".[litellm]"` (recommended)
3. Run `python test_bpui.py` to verify
4. Launch with `bpui` or `./run_bpui.sh`
5. Configure via Settings screen or edit `.bpui.toml`

## Integration Points

### With Existing Repo

- **Blueprints**: Loads from `blueprints/` folder (`rpbotgenerator.md`) and `tools/` folder (`seed-gen.md`)
- **Validator**: Calls `tools/validate_pack.py` via subprocess
- **Export**: Calls `tools/export_character.sh` via subprocess
- **Fixtures**: Compatible with existing `fixtures/sample_pack/` structure

### Output Compatibility

- **Drafts**: Match export contract filenames exactly
- **Exports**: Uses same sanitization logic as `tools/export_character.sh`
- **Validation**: Passes/fails based on existing validator rules

## Testing Verification

`test_bpui.py` verifies:

- All modules import successfully
- Config loads from defaults or `.bpui.toml`
- Codeblock extraction works
- 7-block parsing works
- Character name extraction (via regex test)

## Documentation Delivered

1. **bpui/README.md**: Full module documentation, architecture, usage examples
2. **INSTALL.md**: Step-by-step installation, provider setups, troubleshooting
3. **test_bpui.py**: Executable installation verification
4. **Updated main README.md**: Added "Quick Start" section with TUI option

## Known Limitations & Future Enhancements

### Current Limitations

- No in-TUI editing of assets (read-only tabs in Review screen)
- No draft deletion from TUI (can be added to Drafts screen)
- No batch compilation (one seed at a time)
- No progress bars for long operations (Textual limitation with async streaming)

### Future Enhancement Ideas

- Asset editing in Review screen (add edit mode to TextArea widgets)
- Batch compilation queue
- Draft comparison view (side-by-side diff)
- Export preview before writing
- Custom blueprint paths (currently expects repo root)
- Settings profiles (multiple configs)
- Generation history with re-run capability

## Security Considerations

- API keys stored in environment variables (never in config file)
- `.bpui.toml` gitignored by default
- No credential logging or display in TUI
- Subprocess calls use explicit paths to repo scripts (no shell injection risk)

## Performance Notes

- Streaming reduces perceived latency
- Async HTTP client (httpx) for non-blocking network I/O
- Textual's reactive UI prevents blocking during generation
- Validation/export subprocess calls have 30s timeout

## Maintenance Notes

### Adding a New Screen

1. Create `bpui/tui/new_screen.py` inheriting from `Screen`
2. Define CSS, compose() method, and button handlers
3. Import and push_screen() from relevant navigation point

### Adding a New LLM Adapter

1. Create `bpui/llm/new_engine.py` inheriting from `LLMEngine`
2. Implement `generate()`, `generate_stream()`, `test_connection()`
3. Add to Settings screen Select widget options
4. Update config.py to handle new engine type

### Updating Blueprint Format

1. Update `parse_blocks.py` ASSET_ORDER and ASSET_FILENAMES
2. Update Review screen TabPane labels
3. Update test_bpui.py parser tests
4. Update documentation

## Success Criteria Met

✅ Portable, repo-local terminal application
✅ "Any LLM" support (LiteLLM + OpenAI-compatible)
✅ Streaming output during generation
✅ Strict 7-codeblock parser with Adjustment Note support
✅ Draft management (save, browse, load)
✅ Validation integration
✅ Export integration
✅ Seed generator integration
✅ CLI companion for scripting
✅ Settings persistence (.bpui.toml)
✅ Test connection functionality
✅ Complete documentation

## Running the TUI

```bash
# With venv launcher (auto-setup)
./run_bpui.sh

# Or directly if installed
bpui

# Or with python module
python -m bpui.cli

# CLI mode
bpui compile --seed "..." --mode NSFW
bpui seed-gen --input genres.txt
bpui validate drafts/...
bpui export "Character Name" drafts/...
```

## Conclusion

The Blueprint UI implementation provides a complete, production-ready terminal interface for RPBotGenerator character compilation. It preserves the strict blueprint contract while adding convenient workflows for generation, validation, and export. The dual LLM adapter system ensures compatibility with both hosted providers and local models, meeting the "any LLM" requirement.
