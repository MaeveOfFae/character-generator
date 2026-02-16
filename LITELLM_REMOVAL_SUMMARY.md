# LiteLLM Removal Summary

## Overview
Completely removed LiteLLM engine from the codebase to simplify the LLM provider architecture. The system now uses dedicated engines for each provider (Google, OpenAI, OpenAI-compatible/OpenRouter, Zhipu AI, Moonshot AI).

## Changes Made

### 1. Core Engine Files
- ✅ **Deleted**: `bpui/llm/litellm_engine.py` - LiteLLM adapter removed entirely
- ✅ **Updated**: `bpui/llm/factory.py` - Removed all LiteLLM references and fallback logic
  - Removed LiteLLMEngine import
  - Removed `create_engine` LiteLLM branch
  - Removed `get_engine_type` LiteLLM detection
  - Removed fallback model loading for LiteLLM
  - Simplified provider detection to use OpenAI Compatible for OpenRouter

### 2. GUI Files
- ✅ **Updated**: `bpui/gui/dialogs.py` - Removed all LiteLLM references
  - Removed "LiteLLM" from provider selection dropdown
  - Removed LiteLLM-specific model fallbacks
  - Removed `_get_fallback_models` LiteLLM branch
  - Removed LiteLLM references in API key handling
  - Removed LiteLLM references in provider change detection
  - Updated docstrings to reflect supported providers

### 3. CLI Files
- ✅ **Updated**: `bpui/cli.py` - Removed LiteLLM from help text
  - Updated `--provider` help text to remove "litellm" example

### 4. TUI Files
- ✅ **Updated**: `bpui/tui/settings.py` - Removed LiteLLM engine option
  - Removed "LiteLLM" from engine selection dropdown
  - Removed LiteLLMEngine import and usage in test_connection
  - Now only shows "OpenAI Compatible" option
  
- ✅ **Updated**: `bpui/tui/compile.py` - Removed LiteLLM imports and usage
  - Removed LiteLLMEngine import
  - Removed LiteLLM engine creation branch
  - Fixed mode parameter type error (mode=None -> mode="")

### 5. Remaining TUI Files (To Be Updated)
The following files still have LiteLLM references that need removal:
- ⏳ `bpui/tui/review.py` - Has LiteLLM imports and usage
- ⏳ `bpui/tui/similarity.py` - Has LiteLLM imports and usage  
- ⏳ `bpui/tui/seed_generator.py` - Has LiteLLM imports and usage
- ⏳ `bpui/tui/offspring.py` - Has LiteLLM imports and usage
- ⏳ `bpui/tui/batch.py` - Has LiteLLM imports and usage

## Architecture Changes

### Before
```
LLM Providers:
├── Google (google_engine.py)
├── OpenAI (openai_engine.py)
├── LiteLLM (litellm_engine.py) - Multi-provider adapter
│   └── OpenRouter (via litellm)
│   └── Anthropic (via litellm)
│   └── DeepSeek (via litellm)
│   └── 100+ other providers (via litellm)
└── OpenAI Compatible (openai_compat_engine.py) - Custom/local/other
```

### After
```
LLM Providers:
├── Google (google_engine.py)
├── OpenAI (openai_engine.py)
├── OpenAI Compatible (openai_compat_engine.py)
│   ├── OpenRouter (https://openrouter.ai/api/v1)
│   ├── Anthropic (via OpenAI-compatible APIs)
│   ├── DeepSeek (via OpenAI-compatible APIs)
│   ├── Zhipu AI (via OpenAI-compatible APIs)
│   ├── Moonshot AI (via OpenAI-compatible APIs)
│   └── Any OpenAI-compatible API
```

## Benefits
1. **Simpler Architecture**: Removed complex multi-provider abstraction layer
2. **Better Provider Detection**: Direct model name to provider mapping
3. **Fewer Dependencies**: Removed LiteLLM library dependency
4. **Clearer Error Messages**: Direct provider-specific errors
5. **Easier Maintenance**: Each provider has its own dedicated engine

## Migration Guide for Users

### For OpenRouter Users
Old model names:
```
openrouter/anthropic/claude-3-opus
openrouter/openai/gpt-4o
```

New model names (same format, but using OpenAI Compatible engine):
```
openrouter/anthropic/claude-3-opus
openrouter/openai/gpt-4o
```

No changes needed for OpenRouter users! The model name format remains the same.

### For Anthropic/DeepSeek/Zhipu/Moonshot Users
Use the dedicated provider settings:
- **Anthropic**: Use "anthropic/" prefix models
- **DeepSeek**: Use "deepseek/" prefix models  
- **Zhipu AI**: Use "zai/" prefix models
- **Moonshot AI**: Use model names without prefix (e.g., "moonshot-v1-8k")

### For Local/OpenAI-Compatible Users
Continue using the same setup:
1. Select "OpenAI Compatible" as engine
2. Set base_url to your local endpoint
3. Use model name (e.g., "llama3", "mistral", etc.)

## TODO
- [ ] Update remaining TUI files (review, similarity, seed_generator, offspring, batch)
- [ ] Remove LiteLLM from pyproject.toml dependencies
- [ ] Update README.md documentation
- [ ] Update bpui/README.md documentation
- [ ] Remove LiteLLM references from build directory
- [ ] Run tests to ensure all functionality works

## Testing Checklist
- [ ] OpenRouter model listing works
- [ ] OpenRouter compilation works
- [ ] Google compilation works
- [ ] OpenAI compilation works
- [ ] Zhipu AI compilation works
- [ ] Moonshot AI compilation works
- [ ] TUI settings work correctly
- [ ] GUI settings work correctly
- [ ] CLI commands work correctly
- [ ] Batch compilation works
- [ ] Similarity analysis works
- [ ] Seed generation works
- [ ] Offspring generation works