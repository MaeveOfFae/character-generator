# API Providers

Character Generator supports multiple model providers through the backend configuration and shared API client.

## Primary Provider Paths

- OpenRouter: multi-provider access through the OpenAI-compatible path
- OpenAI: direct OpenAI model usage
- Google: Gemini/Gemma model usage
- Local OpenAI-compatible servers: Ollama, LM Studio, vLLM, and similar endpoints

## Common Config Shape

```toml
[api_keys]
openrouter = "sk-or-v1-..."
openai = "sk-proj-..."
google = "AIzaSy..."

model = "openrouter/anthropic/claude-3.5-sonnet"
base_url = "https://openrouter.ai/api/v1"
temperature = 0.7
max_tokens = 4096
```

Adjust `model` and `base_url` for the provider you actually want to use.

## Common Commands

```bash
bpui list-models --provider openrouter
bpui list-models --provider openai
bpui list-models --provider google
bpui compile --seed "Noir detective with psychic abilities"
```

## Choosing a Provider

- Use OpenRouter when you want one API key for many vendors.
- Use OpenAI when you want direct OpenAI access.
- Use Google when you want Gemini/Gemma models.
- Use a local OpenAI-compatible server when you want local inference.

## Troubleshooting

- Missing key: set the relevant value in `[api_keys]` or export the provider env var.
- Model not found: rerun `bpui list-models --provider ...`.
- Connection issues: verify `base_url` for OpenAI-compatible servers.
- Debug logging: `bpui --log-level DEBUG ...`

## Related Docs

- [openrouter.md](./openrouter.md)
- [openai.md](./openai.md)
- [google.md](./google.md)
- live backend docs at `http://localhost:8000/docs`
