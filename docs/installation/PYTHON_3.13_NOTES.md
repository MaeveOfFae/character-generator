# Python 3.13 Compatibility Notes

## Known Issue: Editable Install Failure

Python 3.13 has a known issue with pip's build isolation when installing packages in editable mode (`pip install -e .`). This affects the `bpui` package installation.

### Error Message

```
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.build_backend'
```

### Root Cause

Pip uses build isolation by default, creating a temporary environment to build packages. In Python 3.13, this isolated environment may fail to properly set up setuptools, even if setuptools is installed in the main venv.

### Workaround Implemented

We've implemented a direct CLI entry point that doesn't require editable installation:

1. **Direct CLI Script**: `bpui-cli`
   - Executable Python script that adds the project root to sys.path
   - Directly imports and runs `bpui.cli.main()`
   - No installation required

2. **Updated Launcher**: `run_bpui.sh`
   - Uses the direct CLI script instead of `python -m bpui.cli`
   - Still creates and manages the venv
   - Installs only direct dependencies

### How to Use

#### Option 1: Launcher Script (Recommended)

```bash
./run_bpui.sh
```

#### Option 2: Direct CLI

```bash
source .venv/bin/activate
./bpui-cli
```

#### Option 3: Via Python

```bash
source .venv/bin/activate
python bpui-cli
```

### All CLI Commands Work

```bash
./bpui-cli tui                    # Launch TUI
./bpui-cli compile --seed "..."   # Compile character
./bpui-cli validate path/to/pack  # Validate
./bpui-cli export "Name" path     # Export
```

### Dependencies Still Required

The following packages must be installed in the venv:

- textual
- rich
- httpx
- tomli-w
- setuptools
- wheel

Optional:

- litellm (for 100+ provider support)

### Future Resolution

This issue may be resolved by:

1. Python 3.13 patch updates
2. Pip updates that fix build isolation
3. Setuptools updates with better Python 3.13 support

Until then, the `bpui-cli` workaround provides full functionality without any limitations.

### Testing

All tests pass with this workaround:

```bash
python test_bpui.py
```

Expected output:

```
✓ All tests passed!
```
