# OpenRouter Model Fetching Fix

## Problem
When switching to OpenRouter provider in the GUI Settings dialog, the model dropdown would remain empty because the code only tried to fetch models if an API key was configured.

## Root Cause
In `bpui/gui/dialogs.py`, the `ModelFetcherThread.run()` method had this logic for OpenRouter:

```python
elif self.provider == "openrouter":
    api_key = self.config.get_api_key("openrouter")
    base_url = "https://openrouter.ai/api/v1"
    if api_key:  # ← PROBLEM: Only fetch if API key exists
        models = loop.run_until_complete(OpenAICompatEngine.list_models(base_url, api_key))
    else:
        models = []  # ← Returns empty list without API key
```

This was inconsistent with how Google and OpenAI providers worked - they always try to fetch from API and only use fallback if the API call fails.

## Solution
Changed OpenRouter to always fetch from the API, even without an API key:

```python
elif self.provider == "openrouter":
    api_key = self.config.get_api_key("openrouter")
    base_url = "https://openrouter.ai/api/v1"
    # Always try to fetch from API, even without API key (like OpenAI/Google do)
    models = loop.run_until_complete(OpenAICompatEngine.list_models(base_url, api_key))
```

## Why This Works

The `OpenAICompatEngine.list_models()` method already handles the case where `api_key=None`:
- It makes a GET request to `{base_url}/models`
- OpenRouter's API returns the full model list even without authentication
- If the API call fails for any reason, the exception handler in `ModelFetcherThread` catches it and uses the fallback models

## Testing Results

```bash
Testing OpenRouter model fetching without API key...
Success! Found 340 models
First 5 models: ['ai21/jamba-large-1.7', 'aion-labs/aion-1.0', 'aion-labs/aion-1.0-mini', 'aion-labs/aion-rp-llama-3.1-8b', 'alfredpros/codellama-7b-instruct-solidity']
```

## Changes Made

### File: `bpui/gui/dialogs.py`
- **Line ~810**: Removed `if api_key:` conditional for OpenRouter
- **Line ~812**: Always call `OpenAICompatEngine.list_models()` even with `api_key=None`
- **Result**: OpenRouter now behaves consistently with OpenAI and Google providers

## User Impact

### Before Fix
1. User opens Settings dialog
2. Selects OpenRadio button for "OpenRouter"
3. Model dropdown shows "Loading models..." then stays empty
4. No models available to select
5. User must manually type model name

### After Fix
1. User opens Settings dialog
2. Selects Radio button for "OpenRouter"
3. Model dropdown shows "Loading models..." briefly
4. Dropdown populates with 340+ OpenRouter models
5. User can select from available models or filter by typing

## Related Code

### Fallback Models (if API fails)
If the API call fails, these fallback models are shown:
```python
[
    "openrouter/anthropic/claude-3-5-sonnet-20241022",
    "openrouter/openai/gpt-4o",
    "openrouter/google/gemini-pro-1.5",
    "openrouter/meta-llama/llama-3-70b-instruct",
]
```

### Engine Type Detection
The `engine_type_label` displays:
- "✓ Loaded {count} models" on success (green)
- "⚠️ Failed to fetch models: {error}" on failure (orange)

## Verification

All three main providers now work consistently:

| Provider | API Call Without Key | Fallback Models | Status |
|----------|---------------------|-----------------|---------|
| OpenRouter | ✅ Yes (340 models) | ✅ Yes (4 models) | ✅ Fixed |
| OpenAI | ❌ Requires key | ✅ Yes (5 models) | ✅ Working |
| Google | ❌ Requires SDK | ✅ Yes (3 models) | ✅ Working |

## Documentation Updates

Created comprehensive provider documentation:
- `docs/api/openrouter.md` - OpenRouter-specific guide
- `docs/api/openai.md` - OpenAI-specific guide  
- `docs/api/google.md` - Google AI-specific guide
- `docs/api/providers.md` - Provider comparison and quick reference

Each guide includes:
- Quick start instructions
- Available models
- Configuration examples
- Model comparison tables
- Best practices
- Troubleshooting tips