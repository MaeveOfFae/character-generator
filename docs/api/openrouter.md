# OpenRouter API Support

Character Generator supports OpenRouter through the OpenAI-compatible backend path.

## Basic Setup

Set your key in the environment or in `.bpui.toml`:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
```

```toml
[api_keys]
openrouter = "sk-or-v1-..."

model = "openrouter/anthropic/claude-3.5-sonnet"
base_url = "https://openrouter.ai/api/v1"
temperature = 0.7
max_tokens = 4096
```

## Model Naming

OpenRouter models use the form `openrouter/{provider}/{model}`.

Examples:

- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/openai/gpt-4o`
- `openrouter/google/gemini-2.5-pro`
- `openrouter/deepseek/deepseek-chat`

## Useful Commands

```bash
# inspect available models
bpui list-models --provider openrouter
bpui list-models --provider openrouter --filter claude
bpui list-models --provider openrouter --format json > models.json

# run a one-off compile
bpui compile --seed "Noir detective with psychic abilities" --model openrouter/anthropic/claude-3.5-sonnet
```

## Notes

- the backend uses the OpenAI-compatible engine for OpenRouter models
- listed model IDs may omit the `openrouter/` prefix; add it back in your config
- the OpenRouter path is the current recommended way to access many providers from one key

## Troubleshooting

- If the model is not found, run `bpui list-models --provider openrouter`.
- If authentication fails, verify `OPENROUTER_API_KEY` or `[api_keys].openrouter`.
- If you need to inspect the live backend behavior, use `http://localhost:8000/docs`.
