# List Models Command Implementation

## Overview
Added a new CLI command `list-models` to list available AI models from OpenAI-compatible APIs, including OpenRouter, OpenAI, Google, and custom endpoints.

## Implementation Details

### Files Modified

1. **bpui/cli.py**
   - Added `list-models` subparser with arguments:
     - `--provider`: Specify provider (openrouter, openai, google, etc.)
     - `--base-url`: Custom base URL for OpenAI-compatible APIs
     - `--api-key`: API key for authentication
     - `--format`: Output format (text, json, csv)
     - `--filter`: Filter models by name/pattern
   
   - Added `run_list_models()` async function that:
     - Determines base URL and API key from provider or config
     - Calls `OpenAICompatEngine.list_models()` static method
     - Filters models if filter pattern specified
     - Outputs results in requested format (text/json/csv)

2. **bpui/llm/openai_compat_engine.py**
   - Already contained `list_models()` static method
   - Makes GET request to `{base_url}/models` endpoint
   - Returns list of model IDs from OpenAI-compatible API response

3. **docs/OPENROUTER_SUPPORT.md**
   - Added "Listing Available Models" section
   - Documented all command options and usage examples

## Usage Examples

### Basic Usage
```bash
# List all OpenRouter models
./bpui-cli list-models --provider openrouter

# List models with API key
./bpui-cli list-models --provider openrouter --api-key sk-or-v1-...
```

### Filtering
```bash
# Filter by pattern (e.g., Claude models only)
./bpui-cli list-models --provider openrouter --filter claude

# Filter for GPT-4 models
./bpui-cli list-models --provider openrouter --filter gpt-4
```

### Output Formats
```bash
# Text format (default)
./bpui-cli list-models --provider openrouter

# JSON format for scripting
./bpui-cli list-models --provider openrouter --format json

# CSV format
./bpui-cli list-models --provider openrouter --format csv
```

### Custom Endpoints
```bash
# Use custom base URL
./bpui-cli list-models --base-url https://api.example.com/v1

# With API key
./bpui-cli list-models --base-url https://api.example.com/v1 --api-key your-key
```

## API Integration

The command uses the OpenAI-compatible API's `/models` endpoint:

```python
async def list_models(base_url: str, api_key: str | None = None, timeout: float = 30.0) -> list[str]:
    """List available models from OpenAI-compatible API."""
    # Makes GET request to {base_url}/models
    # Returns list of model IDs from response.data array
```

This endpoint is documented at:
- OpenRouter: https://openrouter.ai/docs/api/api-reference/models/get-models
- OpenAI: https://platform.openai.com/docs/api-reference/models/list

## Base URL Detection Logic

The implementation uses a clear, 4-step process to determine the base URL:

1. **Step 1: Determine Provider**
   - From `--provider` argument (if specified)
   - Inferred from `--base-url` (e.g., "openrouter.ai" → "openrouter")
   - Falls back to config model prefix

2. **Step 2: Determine Base URL**
   - From `--base-url` argument (if specified)
   - From provider defaults:
     - `openrouter` → `https://openrouter.ai/api/v1`
     - `openai` → `https://api.openai.com/v1`
     - `google` → `https://generativelanguage.googleapis.com/v1beta`
   - From config model prefix (e.g., `openrouter/` → OpenRouter URL)

3. **Step 3: Determine API Key**
   - From `--api-key` argument (if specified)
   - From provider-specific config (e.g., `config.get_api_key("openrouter")`)
   - May be optional for some providers

4. **Step 4: Validation**
   - Ensures base URL is present
   - Displays what will be used
   - Provides helpful error messages

## Debug Logging

The implementation includes comprehensive debug logging:

```bash
# Enable debug logging to see the decision process
./bpui-cli --log-level DEBUG list-models --provider openrouter
```

This helps troubleshoot issues by showing:
- Which arguments were provided
- How provider was determined
- How base URL was determined
- Whether API key was found

## Error Handling

The implementation handles:
- Missing base URL (provides helpful error message)
- Empty model lists
- API request failures (with detailed error messages)
- Filter pattern matching (case-insensitive)
- Multiple output formats

## Testing

To test the implementation:

```bash
# Show help
./bpui-cli list-models --help

# Test with OpenRouter (requires API key)
./bpui-cli list-models --provider openrouter --filter claude

# Test JSON output
./bpui-cli list-models --provider openrouter --format json | head -20
```

## Integration with Config

The command intelligently uses configuration:
- Falls back to config's `model` to detect OpenRouter
- Uses config's `base_url` if available
- Retrieves API key from provider-specific config or general config
- Supports environment variables for API keys

## Benefits

1. **Discoverability**: Users can easily browse available models
2. **Validation**: Verify model names before using them
3. **Scripting**: JSON/CSV output enables automation
4. **Flexibility**: Works with any OpenAI-compatible API
5. **Filtering**: Quickly find specific model families

## Future Enhancements

Potential improvements:
- Add pagination support for large model lists
- Show pricing information if available
- Display model capabilities (context window, etc.)
- Cache model list to reduce API calls
- Add interactive model selector