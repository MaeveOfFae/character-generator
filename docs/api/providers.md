# API Providers Documentation

Character Generator supports multiple AI providers through different engines. This documentation covers each provider's configuration, available models, and best practices.

## Supported Providers

- [OpenRouter](./openrouter.md) - Unified API for multiple AI providers (340+ models)
- [OpenAI](./openai.md) - OpenAI's GPT and O1 models
- [Google AI](./google.md) - Google's Gemini and Gemma models

## Quick Reference

### Listing Available Models

Use the `list-models` command to see available models from any provider:

```bash
# List OpenRouter models
./bpui-cli list-models --provider openrouter

# List OpenAI models
./bpui-cli list-models --provider openai

# List Google models
./bpui-cli list-models --provider google

# Filter by model family
./bpui-cli list-models --provider openrouter --filter claude

# Output to JSON
./bpui-cli list-models --provider openrouter --format json

# Output to CSV
./bpui-cli list-models --provider openrouter --format csv
```

### Model Format Comparison

| Provider | Model Format | Example | Engine |
|----------|--------------|-----------|----------|
| OpenRouter | `openrouter/{provider}/{model}` | `openrouter/anthropic/claude-3-opus` | OpenAICompat |
| OpenAI | `{model-name}` | `gpt-4` | OpenAI Engine |
| Google | `{model-name}` | `gemini-2.0-flash` | Google Engine |
| LiteLLM | `{provider}/{model}` | `anthropic/claude-3-opus` | LiteLLM |

### Choosing a Provider

#### OpenRouter
- **Best for**: Accessing multiple providers through one API, comparing models, unified billing
- **Models**: 340+ models from Anthropic, OpenAI, Google, Meta, Mistral, DeepSeek, and more
- **Documentation**: [Full Guide](./openrouter.md)

#### OpenAI
- **Best for**: Direct OpenAI account usage, highest quality GPT models, latest features
- **Models**: GPT-4, GPT-4o, GPT-3.5, O1 series
- **Documentation**: [Full Guide](./openai.md)

#### Google AI
- **Best for**: Fast, cost-effective models, large context (1M tokens)
- **Models**: Gemini 2.x, Gemma 3.x
- **Documentation**: [Full Guide](./google.md)

## Common Configuration

### API Keys

Set API keys in config or environment:

```bash
# Config file
bpui config set api_keys.{provider} your-key

# Environment variable
export {PROVIDER}_API_KEY="your-key"
```

Supported providers: `openrouter`, `openai`, `google`, `anthropic`, `cohere`, etc.

### Model Parameters

Common parameters across all providers:

```toml
[model]
model = "your-model-name"
temperature = 0.7        # 0.0 to 1.0 (or 2.0 for Google)
max_tokens = 4096        # Maximum tokens to generate
```

### Temperature Guide

- **0.0-0.3**: Factual, technical content
- **0.4-0.7**: Balanced output (default)
- **0.8-1.0**: Creative, varied output
- **1.1-2.0**: Very creative (Google AI only)

### Context Windows

Different models have different context limits:
- OpenRouter: Varies by model (up to 200K tokens)
- OpenAI: 16K-200K tokens depending on model
- Google: 8K-1M tokens depending on model

Check provider documentation for specific limits and recommended `max_tokens` settings.

## Troubleshooting

### Common Issues

**No API key configured**
```bash
bpui config set api_keys.{provider} your-key
```

**Model not found**
```bash
# Verify model name
./bpui-cli list-models --provider {provider}
```

**Rate limit errors**
1. Check provider plan limits
2. Use a smaller/faster model
3. Reduce concurrent requests

**Connection errors**
1. Check internet connection
2. Verify API key is valid
3. Check provider status page

### Debug Mode

Enable debug logging to troubleshoot:

```bash
./bpui-cli --log-level DEBUG compile seed.txt
```

## Support

For provider-specific issues, see individual documentation:
- [OpenRouter Guide](./openrouter.md) - [Status](https://status.openrouter.ai/)
- [OpenAI Guide](./openai.md) - [Status](https://status.openai.com/)
- [Google AI Guide](./google.md) - [Status](https://status.cloud.google.com/)

For general issues:
- [Character Generator GitHub](https://github.com/MaeveOfFae/character-generator/issues)
- [Main Documentation](../README.md)