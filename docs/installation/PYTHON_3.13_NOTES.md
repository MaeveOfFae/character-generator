# Python 3.13 Compatibility Notes

These notes apply to Python-side setup only. The web and Tauri desktop workflows still depend on the same backend environment, but the most common failure mode on Python 3.13 is still editable install friction.

## Known Failure Mode

Some Python 3.13 environments still hit editable-install failures such as:

```text
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.build_backend'
```

## Recommended Paths

### Preferred

Use the repo launchers after creating the venv and installing requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

If that succeeds, use the normal commands:

```bash
./run_bpui.sh
./run_bpui.sh tui
./run_desktop.sh
```

### Fallback if `pip install -e .` fails

The repo includes a direct script at `scripts/bpui-cli`.

```bash
source .venv/bin/activate
python scripts/bpui-cli --help
python scripts/bpui-cli tui
python scripts/bpui-cli compile --seed "..."
```

This bypasses the editable-install entrypoint while still running the current CLI code.

## Notes

- `run_bpui.sh` now runs `python -m bpui.core.cli`
- the fallback script is useful when packaging/entrypoint installation is the part that breaks
- the desktop launcher still expects the Python dependencies from `requirements.txt`

## Validation

If you are testing on Python 3.13, these are the most useful checks:

```bash
pytest -m "not slow"
python -m uvicorn bpui.api.main:app --reload
pnpm --filter @char-gen/web exec tsc --noEmit
```
