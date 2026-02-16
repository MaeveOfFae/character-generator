# z.ai and Moonshot AI Implementation Update Summary

## Overview
Updated both z.ai (Zhipu AI GLM) and Moonshot AI (Kimi) implementations to use current model names as documented in their respective platforms:
- [z.ai FAQ](https://docs.z.ai/devpack/faq)
- [Moonshot AI Overview](https://platform.moonshot.ai/docs/overview)

## Changes Made

### 1. Model Name Updates (bpui/gui/dialogs.py)
Updated from old `zhipuai/glm-*` format to new `zai/glm-*` format:

**Old Models:**
- zhipuai/glm-4
- zhipuai/glm-4-flash
- zhipuai/glm-4-plus
- zhipuai/glm-4-0520
- zhipuai/glm-3-turbo
- zhipuai/glm-3

**New Models:**
- zai/glm-5
- zai/glm-4.7
- zai/glm-4.6
- zai/glm-4.5
- zai/glm-4.5-air
- zai/glm-4.5-flash
- zai/glm-4.5v
- zai/glm-4.5-x

Updated in two locations:
1. `ModelFetcherThread.run()` - main model list for the provider
2. `ModelFetcherThread._get_fallback_models()` - fallback models when API fails

### 2. Moonshot AI Model Updates (bpui/gui/dialogs.py)
Updated Moonshot AI (Kimi) models to current version:

**Updated Models:**
- moonshot-v1-8k
- moonshot-v1-32k
- moonshot-v1-128k
- moonshot-v1-8k-20240515
- moonshot-v1-32k-20240515
- moonshot-v1-128k-20240515

Updated in two locations:
1. `ModelFetcherThread.run()` - main model list for the provider
2. `ModelFetcherThread._get_fallback_models()` - fallback models when API fails

### 3. Provider Detection (bpui/llm/factory.py)
Added provider detection for both zai and moonshot in `detect_provider_from_model()` function:
- Models starting with `zai/` are now detected as `zai` provider
- Models starting with `moonshot-` are now detected as `moonshot` provider
- Added documentation examples in docstring
- Ensures both providers are checked before generic litellm provider

### 4. Engine Creation (bpui/llm/factory.py)
Added explicit handling for both providers in `create_engine()` function:

**For zai:**
- zai models use LiteLLM engine
- Requires LiteLLM to be installed
- API key is fetched from `api_keys.zai` config
- Provides clear error messages if LiteLLM is not installed

**For moonshot:**
- moonshot models use LiteLLM engine
- Requires LiteLLM to be installed
- API key is fetched from `api_keys.moonshot` config
- Provides clear error messages if LiteLLM is not installed

### 5. Engine Type Detection (bpui/llm/factory.py)
Updated `get_engine_type()` function:
- Returns "LiteLLMEngine" for zai provider
- Returns "LiteLLMEngine" for moonshot provider
- Ensures UI displays correct engine type for both models

## Verification

All tests passed:
- ✓ Provider detection correctly identifies zai models
- ✓ Provider detection correctly identifies moonshot models
- ✓ Engine type detection returns correct type for both
- ✓ GUI model lists updated with new model names for both
- ✓ Fallback models include current models for both
- ✓ Existing providers (google, openai, openrouter, anthropic) continue to work

## API Key Configuration

**For z.ai:**
```bash
bpui config set api_keys.zai YOUR_API_KEY
```

**For Moonshot AI:**
```bash
bpui config set api_keys.moonshot YOUR_API_KEY
```

Or through the GUI Settings dialog when the respective provider is selected.

## Usage Examples

### CLI - z.ai
```bash
bpui config set model zai/glm-5
bpui config set api_keys.zai your_api_key_here
```

### CLI - Moonshot AI
```bash
bpui config set model moonshot-v1-128k
bpui config set api_keys.moonshot your_api_key_here
```

### Python API
```python
from bpui.llm.factory import create_engine

# z.ai
engine = create_engine(
    config,
    model="zai/glm-4.7",
    temperature=0.7
)

# Moonshot AI
engine = create_engine(
    config,
    model="moonshot-v1-128k",
    temperature=0.7
)
```

## Model Details

### z.ai Models
- **zai/glm-5** - Latest flagship model
- **zai/glm-4.7** - High-performance model
- **zai/glm-4.6** - Previous generation
- **zai/glm-4.5** - Balanced model
- **zai/glm-4.5-air** - Lightweight version
- **zai/glm-4.5-flash** - Fast response model
- **zai/glm-4.5v** - Vision-capable model
- **zai/glm-4.5-x** - Specialized model

### Moonshot AI Models
- **moonshot-v1-8k** - 8k context window
- **moonshot-v1-32k** - 32k context window
- **moonshot-v1-128k** - 128k context window
- **moonshot-v1-8k-20240515** - 8k version (May 2024)
- **moonshot-v1-32k-20240515** - 32k version (May 2024)
- **moonshot-v1-128k-20240515** - 128k version (May 2024)

All models are supported through LiteLLM and follow the standard chat API interface.

## Backward Compatibility

**Breaking Change:** Old z.ai model names (`zhipuai/glm-*`) are no longer supported in the model lists. Users should update their configuration to use the new `zai/glm-*` format.

Moonshot AI model names remain compatible.

## Files Modified

1. `bpui/gui/dialogs.py` - Updated model lists for zai and moonshot providers
2. `bpui/llm/factory.py` - Added zai and moonshot provider detection and handling

## Related Documentation

- [z.ai FAQ](https://docs.z.ai/devpack/faq) - Official z.ai documentation
- [Moonshot AI Overview](https://platform.moonshot.ai/docs/overview) - Official Moonshot AI documentation
- [LiteLLM Documentation](https://docs.litellm.ai/) - For additional model parameters
