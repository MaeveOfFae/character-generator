# OpenAI API Support

Character Generator supports [OpenAI](https://openai.com/) models through both native OpenAI SDK and OpenAI-compatible API engine.

## Quick Start

### 1. Set your OpenAI API key

```bash
# Set via environment variable
export OPENAI_API_KEY="your-openai-key"

# Or set via config
bpui config set api_keys.openai your-openai-key
```

### 2. Configure your model

Edit `.bpui.toml`:

```toml
[model]
model = "gpt-4"
temperature = 0.7
max_tokens = 4096
```

### 3. Run character generation

```bash
bpui compile template.toml
```

## Available Models

### GPT-4 Series
- `gpt-4` - Most capable GPT-4 model
- `gpt-4-turbo` - Faster GPT-4 with vision
- `gpt-4-turbo-preview` - Latest GPT-4 Turbo
- `gpt-4o` - Multimodal flagship model
- `gpt-4o-mini` - Smaller, faster GPT-4o

### GPT-3.5 Series
- `gpt-3.5-turbo` - Fast and efficient
- `gpt-3.5-turbo-16k` - Extended context
- `gpt-3.5-turbo-instruct` - Instruction-tuned

### O1 Series (Reasoning)
- `o1-preview` - Advanced reasoning
- `o1-mini` - Faster reasoning
- `o3` - Latest reasoning model

### Listing All Available Models

Use the CLI to list all available OpenAI models:

```bash
# List all OpenAI models
./bpui-cli list-models --provider openai

# Filter by model family
./bpui-cli list-models --provider openai --filter gpt-4
./bpui-cli list-models --provider openai --filter gpt-3.5
./bpui-cli list-models --provider openai --filter o1

# Output to JSON
./bpui-cli list-models --provider openai --format json > models.json
```

## Configuration

### Using OpenAI as Default

```toml
[api_keys]
openai = "sk-proj-..."

[model]
model = "gpt-4"
temperature = 0.7
max_tokens = 4096
```

### Model Parameters

```toml
[model]
model = "gpt-4"
temperature = 0.7        # 0.0 to 1.0 (higher = more creative)
max_tokens = 4096        # Maximum tokens to generate
```

### Engine Selection

Character Generator automatically uses the native OpenAI SDK for OpenAI models. No special configuration needed.

## CLI Usage

```bash
# Set OpenAI as default model
bpui config set model gpt-4
bpui config set api_keys.openai sk-proj-...

# Compile with OpenAI model (one-time)
bpui compile template.toml --model gpt-4

# Test connection
bpui config test-connection --model gpt-4
```

## Model Comparison

| Model | Context | Speed | Best For |
|--------|----------|---------|-----------|
| gpt-4 | 128K | Slow | Complex reasoning, creative writing |
| gpt-4-turbo | 128K | Medium | Balance of speed and quality |
| gpt-4o | 128K | Fast | Multimodal, general use |
| gpt-4o-mini | 128K | Very Fast | Quick responses, cost-effective |
| gpt-3.5-turbo | 16K | Very Fast | Simple tasks, chat |
| o1-preview | 200K | Slow | Complex reasoning, math, coding |
| o1-mini | 200K | Medium | Faster reasoning tasks |

## Best Practices

### Choose Models by Use Case

- **Creative writing**: `gpt-4`, `gpt-4o`
- **Code generation**: `gpt-4o`, `o1-preview`
- **Fast responses**: `gpt-4o-mini`, `gpt-3.5-turbo`
- **Complex reasoning**: `o1-preview`, `o1`
- **Multimodal**: `gpt-4o` (supports images)

### Temperature Settings

```toml
# For creative writing (higher temperature)
[model]
model = "gpt-4"
temperature = 0.9

# For factual/technical content (lower temperature)
[model]
model = "gpt-4"
temperature = 0.3

# For balanced output
[model]
model = "gpt-4"
temperature = 0.7
```

### Context Windows

- GPT-4, GPT-4o: 128K tokens
- GPT-3.5 Turbo: 16K tokens
- O1 series: 200K tokens

Set `max_tokens` appropriately:

```toml
model = "gpt-4"
max_tokens = 8000  # Reasonable output length
```

## Troubleshooting

### No API Key Configured

```bash
bpui config set api_keys.openai your-api-key
```

Or use environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Model Not Found

Verify model name using:

```bash
./bpui-cli list-models --provider openai
```

### Rate Limit Errors

1. Check your OpenAI plan limits
2. Use a smaller/faster model
3. Add delays between requests in batch mode

### Quota Exceeded

Check your usage at [OpenAI Dashboard](https://platform.openai.com/usage)

## References

- [OpenAI Documentation](https://platform.openai.com/docs)
- [OpenAI Models](https://platform.openai.com/docs/models)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [OpenAI Pricing](https://openai.com/pricing)
- [OpenAI Status](https://status.openai.com/)