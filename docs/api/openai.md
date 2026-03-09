# OpenAI API Support

Character Generator can use OpenAI models directly through the Python backend.

## Basic Setup

Set your key in the environment or in `.bpui.toml`:

```bash
export OPENAI_API_KEY="your-openai-key"
```

```toml
[api_keys]
openai = "sk-proj-..."

model = "gpt-4o"
temperature = 0.7
max_tokens = 4096
```

## Useful Commands

```bash
# inspect available models
bpui list-models --provider openai
bpui list-models --provider openai --filter gpt-4

# run a one-off compile
bpui compile --seed "Noir detective with psychic abilities" --model gpt-4o
```

## Notes

- use plain OpenAI model names such as `gpt-4o` or `gpt-4.1`
- OpenAI-specific settings still flow through the shared backend config
- for a live connection check, use the app settings UI or the backend config test endpoint

## Troubleshooting

- If the model is not found, run `bpui list-models --provider openai`.
- If requests fail, verify `OPENAI_API_KEY` or the `[api_keys].openai` value.
- For focused debugging, use `bpui --log-level DEBUG ...`.
