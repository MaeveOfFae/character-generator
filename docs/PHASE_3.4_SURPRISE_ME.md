# Phase 3.4: AI-Powered Seed Enhancement

## Feature: "Surprise Me" Mode

**Status:** ✅ Complete

### What It Does

Adds a "Surprise Me" button to the Seed Generator that generates completely random, creative character seeds using LLM without requiring any genre input from the user.

### Implementation Details

#### Modified Files

- **bpui/gui/seed_generator.py** (320 lines)
  - Added `surprise_mode` parameter to `SeedGenWorker.__init__()`
  - Modified `_generate()` to support two modes:
    - **Standard mode:** Uses `build_seedgen_prompt()` with user-provided genre lines
    - **Surprise mode:** Uses custom prompt that generates 12 diverse character seeds across genres
  - Added "🎲 Surprise Me!" button with teal color scheme
  - Added `surprise_me()` method that triggers worker in surprise mode
  - Added "← Back" button for navigation
  - Updated all button enable/disable logic to include `surprise_btn`

#### Surprise Mode Prompt

The surprise mode uses a carefully crafted prompt that:
- Generates exactly 12 creative character concepts
- Mixes multiple genres (fantasy, sci-fi, horror, noir, cyberpunk, romance, thriller, historical)
- Includes power dynamics, personality quirks, conflicts, or unique hooks
- Provides specific details that spark imagination
- Avoids numbering or commentary

Example output format:
```
Clockwork assassin haunted by memories of their human life
Fae debt collector who trades in secrets instead of gold
Retired superhero running a dive bar in the bad part of town
Moreau bartender with canine traits, secretly investigates missing persons cases
```

### User Experience

1. User clicks "🎲 Surprise Me!" button
2. Status shows "⏳ Generating surprise seeds..."
3. Both Generate and Surprise Me buttons disabled during generation
4. Cancel button becomes active
5. After generation completes:
   - Seeds appear in list (12 diverse concepts)
   - Status shows "✓ Generated 12 seeds"
   - All buttons re-enabled
6. User can double-click any seed to use in Compile screen

### Benefits

- **Zero-friction exploration:** No genre input required
- **Creative diversity:** LLM generates varied concepts across genres
- **Inspiration tool:** Helps users discover unexpected character ideas
- **Same workflow:** Integrates seamlessly with existing seed generator

### Technical Notes

- **Thread safety:** Uses QThread worker pattern (same as standard mode)
- **Error handling:** Same error handling as genre-based generation
- **Cancellation:** Supports cancel during generation
- **LLM integration:** Uses same LiteLLMEngine as all other features

### Testing

To test:
1. Open GUI: `./run_bpui.sh`
2. Go to Seed Generator screen
3. Click "🎲 Surprise Me!" button
4. Verify 12 diverse seeds are generated
5. Double-click any seed → should populate Compile screen
6. Test cancel during generation
7. Test back button navigation

### Priority

**LOW PRIORITY** - Fun experimentation feature for creative exploration.

### Future Enhancements (Optional)

Possible additions:
- Variety mode selector (random, archetype-based, trope-subversion)
- Seed diversity slider (safe → experimental)
- Save favorite seeds to collection
- Seed refinement ("more like this")
