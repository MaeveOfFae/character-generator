# OpenRouter API Support

Character Generator supports [OpenRouter](https://openrouter.ai/) through the OpenAI-compatible API engine. OpenRouter provides access to multiple AI models from various providers through a single API.

## Quick Start

### 1. Set your OpenRouter API key

```bash
# Set via environment variable
export OPENROUTER_API_KEY="your-openrouter-key"

# Or set via config
bpui config set api_keys.openrouter your-openrouter-key
```

### 2. Configure your model

Edit `.bpui.toml`:

```toml
[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7
max_tokens = 4096
```

### 3. Run character generation

```bash
bpui compile template.toml
```

## Available Models

OpenRouter models follow the format: `openrouter/{provider}/{model-name}`

### Popular Model Families

#### Anthropic
- `openrouter/anthropic/claude-3-opus`
- `openrouter/anthropic/claude-3-sonnet`
- `openrouter/anthropic/claude-3-haiku`
- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/anthropic/claude-opus-4`

#### OpenAI
- `openrouter/openai/gpt-3.5-turbo`
- `openrouter/openai/gpt-4`
- `openrouter/openai/gpt-4-turbo`
- `openrouter/openai/gpt-4o`
- `openrouter/openai/gpt-5`

#### Google
- `openrouter/google/gemini-2.0-flash`
- `openrouter/google/gemini-2.5-pro`
- `openrouter/google/gemini-3-pro`
- `openrouter/google/gemma-3-27b-it`

#### Meta Llama
- `openrouter/meta-llama/llama-3-70b-instruct`
- `openrouter/meta-llama/llama-3.1-405b-instruct`
- `openrouter/meta-llama/llama-3.3-70b-instruct`
- `openrouter/meta-llama/llama-4-maverick`

#### DeepSeek
- `openrouter/deepseek/deepseek-chat`
- `openrouter/deepseek/deepseek-r1`
- `openrouter/deepseek/deepseek-v3.2`

#### Mistral
- `openrouter/mistralai/mistral-large`
- `openrouter/mistralai/mistral-medium-3`
- `openrouter/mistralai/mixtral-8x22b-instruct`

### Listing All Available Models

Use the CLI to list all available OpenRouter models:

```bash
./bpui-cli list-models --provider openrouter

# Filter by model family
./bpui-cli list-models --provider openrouter --filter claude
./bpui-cli list-models --provider openrouter --filter gpt-4
./bpui-cli list-models --provider openrouter --filter gemini

# Output to JSON
./bpui-cli list-models --provider openrouter --format json > models.json
```

**Note**: Model IDs are listed without the `openrouter/` prefix. Add it when using models in your config.

## Configuration

### Using OpenRouter as Default

```toml
[api_keys]
openrouter = "sk-or-v1-..."

[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7
max_tokens = 4096
```

### Provider-Specific Keys

OpenRouter supports keys for specific providers:

```toml
[api_keys]
openrouter = "sk-or-v1-..."    # OpenRouter key (recommended)
openai = "sk-..."               # For OpenAI models
anthropic = "sk-ant-..."         # For Anthropic models
google = "AIzaSy..."             # For Google models
```

### Model Parameters

```toml
[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7        # 0.0 to 1.0 (higher = more creative)
max_tokens = 4096        # Maximum tokens to generate
```

## CLI Usage

```bash
# Set OpenRouter as default model
bpui config set model openrouter/anthropic/claude-3-opus
bpui config set api_keys.openrouter sk-or-v1-...

# Compile with OpenRouter model (one-time)
bpui compile template.toml --model openrouter/anthropic/claude-3-opus

# Test connection
bpui config test-connection --model openrouter/anthropic/claude-3-opus
```

## Benefits

1. **Unified API**: Access multiple AI providers through a single API
2. **Model Aggregation**: Browse models from different providers in one place
3. **Fallback & Routing**: Automatic routing to best available model
4. **Cost Comparison**: Compare pricing across providers
5. **Simplified Billing**: Single billing interface

## Best Practices

### Choose Models by Use Case

- **Creative writing**: Claude 3 Opus, GPT-4
- **Code generation**: GPT-4 Turbo, DeepSeek Coder, Claude 3 Sonnet
- **Fast responses**: GPT-3.5 Turbo, smaller models
- **Budget-conscious**: Meta Llama, Mistral

### Context Windows

- Claude 3 Opus: 200K tokens
- GPT-4: 128K tokens
- GPT-3.5 Turbo: 16K tokens
- Llama 3 70B: 128K tokens

Set `max_tokens` appropriately:

```toml
model = "openrouter/anthropic/claude-3-opus"
max_tokens = 100000  # Within the model's limit
```

## Troubleshooting

### No API Key Configured

```bash
bpui config set api_keys.openrouter your-api-key
```

Or use environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key"
```

### Model Not Found

Verify the model name using:

```bash
./bpui-cli list-models --provider openrouter
```

Model names are case-sensitive.

### Rate Limit Errors

1. Upgrade your OpenRouter plan
2. Use a different model
3. Adjust batch settings to reduce concurrent requests

## References

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/pricing)
- [OpenRouter Status](https://status.openrouter.ai/)