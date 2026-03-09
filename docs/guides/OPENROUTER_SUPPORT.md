# OpenRouter Support

OpenRouter is the simplest way to use many commercial models with Character Generator through one API key.

## Recommended Config

```toml
[api_keys]
openrouter = "sk-or-v1-..."

model = "openrouter/anthropic/claude-3.5-sonnet"
base_url = "https://openrouter.ai/api/v1"
temperature = 0.7
max_tokens = 4096
```

You can also export the key instead of storing it in `.bpui.toml`:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
```

## Useful Commands

```bash
# inspect models
bpui list-models --provider openrouter
bpui list-models --provider openrouter --filter claude
bpui list-models --provider openrouter --format json > models.json

# compile with a specific model
bpui compile --seed "Noir detective with psychic abilities" --model openrouter/anthropic/claude-3.5-sonnet
```

## Model Naming

Use `openrouter/{provider}/{model}` in config and CLI overrides.

Examples:

- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/openai/gpt-4o`
- `openrouter/google/gemini-2.5-pro`
- `openrouter/deepseek/deepseek-chat`

## Why Use OpenRouter

- one key for many providers
- quick model comparison
- fewer config changes when switching vendors
- useful for testing Anthropic, OpenAI, Google, and others from the same backend path

## Troubleshooting

- If authentication fails, verify `OPENROUTER_API_KEY` or `[api_keys].openrouter`.
- If a model is missing, rerun `bpui list-models --provider openrouter`.
- If you need deeper inspection, check the live backend docs at `http://localhost:8000/docs`.
