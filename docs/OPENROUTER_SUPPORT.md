# OpenRouter Support

Character Generator supports [OpenRouter](https://openrouter.ai/) through the OpenAI-compatible API engine. OpenRouter provides access to multiple AI models from various providers through a single API that follows the OpenAI chat/completions format.

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
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7
max_tokens = 4096
```

### 3. Run character generation

```bash
bpui compile template.toml
```

## Available OpenRouter Models

OpenRouter models follow the format: `openrouter/{provider}/{model-name}`

### Anthropic Models
- `openrouter/anthropic/claude-3-opus`
- `openrouter/anthropic/claude-3-sonnet`
- `openrouter/anthropic/claude-3-haiku`
- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/anthropic/claude-instant-v1`

### OpenAI Models
- `openrouter/openai/gpt-3.5-turbo`
- `openrouter/openai/gpt-4`
- `openrouter/openai/gpt-4-turbo`
- `openrouter/openai/gpt-4o`
- `openrouter/openai/o1-preview`
- `openrouter/openai/o1-mini`

### Google Models
- `openrouter/google/gemini-pro`
- `openrouter/google/gemini-pro-vision`
- `openrouter/google/palm-2-chat-bison`

### Meta Llama Models
- `openrouter/meta-llama/llama-2-13b-chat`
- `openrouter/meta-llama/llama-2-70b-chat`
- `openrouter/meta-llama/llama-3-70b-instruct`
- `openrouter/meta-llama/codellama-34b-instruct`

### Mistral Models
- `openrouter/mistralai/mistral-7b-instruct`
- `openrouter/mistralai/mistral-large`
- `openrouter/mistralai/mixtral-8x22b-instruct`

### DeepSeek Models
- `openrouter/deepseek/deepseek-chat`
- `openrouter/deepseek/deepseek-coder`

### Other Providers
- Cohere: `openrouter/cohere/command-r-plus`
- Qwen: `openrouter/qwen/qwen-2.5-coder-32b-instruct`
- And many more! Check [OpenRouter's model list](https://openrouter.ai/models) for the complete catalog.

## Configuration Options

### Using OpenRouter as default provider

```toml
[api_keys]
openrouter = "sk-or-v1-..."

[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7
max_tokens = 4096
```

### Setting provider-specific keys

OpenRouter supports multiple underlying providers. You can set keys for specific providers:

```toml
[api_keys]
openrouter = "sk-or-v1-..."           # OpenRouter key (recommended)
openai = "sk-..."                       # For OpenAI models via OpenRouter
anthropic = "sk-ant-..."                 # For Anthropic models via OpenRouter
google = "AIzaSy..."                     # For Google models via OpenRouter
```

The system will automatically use the appropriate key based on the model.

### Engine mode

OpenRouter models are automatically detected and use the OpenAI-compatible API engine. No special configuration needed - just use the model name:

```toml
[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.7
max_tokens = 4096
```

The system will automatically:
1. Detect the `openrouter/` prefix
2. Use the OpenAI-compatible API engine
3. Connect to OpenRouter's endpoint at `https://openrouter.ai/api/v1`

## CLI Usage

### Set OpenRouter as default model

```bash
bpui config set model openrouter/anthropic/claude-3-opus
bpui config set api_keys.openrouter sk-or-v1-...
```

### Compile with OpenRouter model (one-time)

```bash
bpui compile template.toml --model openrouter/openai/gpt-4 --api-key sk-or-v1-...
```

### Test connection

```bash
bpui config test-connection --model openrouter/anthropic/claude-3-opus
```

## Benefits of Using OpenRouter

### 1. **Unified API**
Access multiple AI providers through a single API with consistent response format.

### 2. **Model Aggregation**
Browse and compare models from different providers in one place.

### 3. **Fallback & Routing**
OpenRouter can automatically route requests to the best available model based on cost, speed, or availability.

### 4. **Cost Comparison**
See pricing across providers and choose the best value for your use case.

### 5. **Simplified Billing**
Single billing interface across all providers.

## Best Practices

### 1. Choose models by use case

- **Creative writing**: Claude 3 Opus or GPT-4
- **Code generation**: GPT-4 Turbo, DeepSeek Coder, or Claude 3 Sonnet
- **Fast responses**: GPT-3.5 Turbo or smaller models
- **Budget-conscious**: Meta Llama models or Mistral

### 2. Adjust parameters appropriately

```toml
# For creative writing (higher temperature, more tokens)
[model]
model = "openrouter/anthropic/claude-3-opus"
temperature = 0.9
max_tokens = 8192

# For factual/technical content (lower temperature)
[model]
model = "openrouter/openai/gpt-4"
temperature = 0.3
max_tokens = 4096
```

### 3. Monitor costs

OpenRouter provides detailed usage metrics. Check your [OpenRouter dashboard](https://openrouter.ai/keys) to monitor usage and costs.

### 4. Use appropriate context windows

Different models have different context limits:

- Claude 3 Opus: 200K tokens
- GPT-4: 128K tokens
- GPT-3.5 Turbo: 16K tokens
- Llama 2 70B: 4K tokens

Set `max_tokens` appropriately to avoid errors:

```toml
model = "openrouter/anthropic/claude-3-opus"
max_tokens = 100000  # Within Claude 3's 200K limit
```

## Troubleshooting

### Issue: "No API key configured for model"

**Solution**: Set your OpenRouter API key:

```bash
bpui config set api_keys.openrouter your-api-key
```

Or set environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key"
```

### Issue: Model not found error

**Solution**: Verify the model name against [OpenRouter's model list](https://openrouter.ai/models). Model names are case-sensitive.

### Issue: Rate limit errors

**Solution**: OpenRouter has rate limits. You can:
1. Upgrade your OpenRouter plan
2. Use a different model with higher limits
3. Adjust batch settings to reduce concurrent requests

### Issue: Slow responses

**Solution**: 
1. Check OpenRouter's status page
2. Try a different model or provider
3. Reduce `max_tokens` if you don't need the full output
4. Check your internet connection

## Examples

### Character generation with Claude 3 Opus via OpenRouter

```bash
bpui config set model openrouter/anthropic/claude-3-opus
bpui config set api_keys.openrouter $OPENROUTER_API_KEY
bpui compile my_template.toml
```

### Using GPT-4 via OpenRouter

```bash
bpui compile template.toml \
  --model openrouter/openai/gpt-4 \
  --api-key $OPENROUTER_API_KEY
```

### Testing multiple models

```bash
# Test with Claude 3 Opus
bpui compile template.toml --model openrouter/anthropic/claude-3-opus

# Test with GPT-4
bpui compile template.toml --model openrouter/openai/gpt-4

# Test with Llama 3
bpui compile template.toml --model openrouter/meta-llama/llama-3-70b-instruct
```

## Advanced Usage

### Custom base URL

If you're using a OpenRouter proxy or custom endpoint:

```toml
engine = "litellm"
base_url = "https://your-proxy.com/v1"
model = "openrouter/anthropic/claude-3-opus"
```

### Streaming responses

Streaming works automatically with OpenRouter:

```bash
bpui compile template.toml --stream
```

### Batch processing

OpenRouter supports batch operations. Adjust batch settings:

```toml
[batch]
max_concurrent = 3
rate_limit_delay = 1.0
```

## References

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models List](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/pricing)
- [LiteLLM Documentation](https://docs.litellm.ai/)

## Support

If you encounter issues with OpenRouter support:

1. Check this documentation for common solutions
2. Review [OpenRouter's status page](https://status.openrouter.ai/)
3. Check your API key and billing status
4. Open an issue on the [character-generator GitHub repository](https://github.com/MaeveOfFae/character-generator/issues)