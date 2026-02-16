# Google AI API Support

Character Generator supports [Google AI](https://ai.google.dev/) models through the native Google Generative AI SDK.

## Quick Start

### 1. Set your Google AI API key

```bash
# Set via environment variable
export GOOGLE_API_KEY="your-google-key"

# Or set via config
bpui config set api_keys.google your-google-key
```

### 2. Configure your model

Edit `.bpui.toml`:

```toml
[model]
model = "gemini-2.0-flash"
temperature = 0.7
max_tokens = 8192
```

### 3. Run character generation

```bash
bpui compile template.toml
```

## Available Models

### Gemini 2.0 Series
- `gemini-2.0-flash` - Fast, multimodal
- `gemini-2.0-flash-lite` - Lightweight, faster
- `gemini-2.5-flash` - Enhanced flash model
- `gemini-2.5-pro` - Capable, balanced
- `gemini-2.5-flash-lite` - Latest lightweight flash
- `gemini-3-flash-preview` - Preview of next-gen flash

### Gemma Series
- `gemma-2-27b-it` - 27B parameter model
- `gemma-2-9b-it` - 9B parameter model
- `gemma-3-12b-it` - 12B parameter model
- `gemma-3-27b-it` - 27B parameter model
- `gemma-3-4b-it` - 4B parameter model

### Listing All Available Models

Use the CLI to list available Google models:

```bash
# List all Google models
./bpui-cli list-models --provider google

# Filter by model family
./bpui-cli list-models --provider google --filter gemini
./bpui-cli list-models --provider google --filter gemma

# Output to JSON
./bpui-cli list-models --provider google --format json > models.json
```

## Configuration

### Using Google AI as Default

```toml
[api_keys]
google = "AIzaSy..."

[model]
model = "gemini-2.0-flash"
temperature = 0.7
max_tokens = 8192
```

### Model Parameters

```toml
[model]
model = "gemini-2.0-flash"
temperature = 0.7        # 0.0 to 2.0 (higher = more creative)
max_tokens = 8192        # Maximum tokens to generate
```

### Engine Selection

Character Generator automatically uses the native Google Generative AI SDK for Google models. No special configuration needed.

## CLI Usage

```bash
# Set Google AI as default model
bpui config set model gemini-2.0-flash
bpui config set api_keys.google AIzaSy...

# Compile with Google model (one-time)
bpui compile template.toml --model gemini-2.0-flash

# Test connection
bpui config test-connection --model gemini-2.0-flash
```

## Model Comparison

| Model | Context | Speed | Best For |
|--------|----------|---------|-----------|
| gemini-2.0-flash | 1M | Very Fast | Quick responses, general tasks |
| gemini-2.5-pro | 1M | Medium | Complex reasoning, creative writing |
| gemini-2.5-flash | 1M | Fast | Balance of speed and quality |
| gemini-3-flash-preview | 1M | Very Fast | Latest features, experimental |
| gemma-3-27b-it | 8K | Medium | Efficient, open model |
| gemma-3-4b-it | 8K | Very Fast | Lightweight, fast responses |

## Best Practices

### Choose Models by Use Case

- **Fast responses**: `gemini-2.0-flash`, `gemini-2.5-flash`
- **Creative writing**: `gemini-2.5-pro`, `gemini-3-flash-preview`
- **Complex reasoning**: `gemini-2.5-pro`
- **Cost-effective**: `gemma-3-4b-it`, `gemma-3-12b-it`
- **Large context**: Any Gemini 2.x model (1M context)

### Temperature Settings

Google supports a wider temperature range (0.0 to 2.0):

```toml
# For creative writing (higher temperature)
[model]
model = "gemini-2.5-pro"
temperature = 1.2

# For factual/technical content (lower temperature)
[model]
model = "gemini-2.5-pro"
temperature = 0.3

# For balanced output
[model]
model = "gemini-2.5-pro"
temperature = 0.7
```

### Context Windows

- Gemini 2.x series: 1M tokens
- Gemma series: 8K tokens

Set `max_tokens` appropriately:

```toml
model = "gemini-2.0-flash"
max_tokens = 32000  # Reasonable output length
```

## Troubleshooting

### No API Key Configured

```bash
bpui config set api_keys.google your-api-key
```

Or use environment variable:

```bash
export GOOGLE_API_KEY="your-api-key"
```

### Model Not Found

Verify model name using:

```bash
./bpui-cli list-models --provider google
```

Model names are case-sensitive.

### Rate Limit Errors

1. Check your Google AI plan limits
2. Use a smaller/faster model
3. Add delays between requests in batch mode

### API Quota Exceeded

Check your usage at [Google AI Studio](https://aistudio.google.com/app/apikey)

## References

- [Google AI Documentation](https://ai.google.dev/docs)
- [Google AI Models](https://ai.google.dev/models)
- [Google AI API Reference](https://ai.google.dev/docs/api)
- [Google AI Pricing](https://ai.google.dev/pricing)
- [Google AI Status](https://status.cloud.google.com/)