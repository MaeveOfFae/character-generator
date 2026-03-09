# Google AI API Support

Character Generator can use Google models through the backend's Google support.

## Basic Setup

Set your key in the environment or in `.bpui.toml`:

```bash
export GOOGLE_API_KEY="your-google-key"
```

```toml
[api_keys]
google = "AIzaSy..."

model = "gemini-2.5-pro"
temperature = 0.7
max_tokens = 8192
```

## Useful Commands

```bash
# inspect available models
bpui list-models --provider google
bpui list-models --provider google --filter gemini

# run a one-off compile
bpui compile --seed "Noir detective with psychic abilities" --model gemini-2.5-pro
```

## Notes

- Gemini and Gemma model names are used directly, without an `openrouter/` prefix
- Google models may support larger temperature or context ranges than other providers
- verify actual available model names with `bpui list-models --provider google`

## Troubleshooting

- If the model is not found, list models again from the current account.
- If requests fail, verify `GOOGLE_API_KEY` or `[api_keys].google`.
- Use `bpui --log-level DEBUG ...` for request-level debugging.
