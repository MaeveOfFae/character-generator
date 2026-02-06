# GitHub Bugs Report
Generated: 2/6/2026, 9:10 AM

## Summary
Found **5 open bug reports** on the GitHub repository.

---

## Issue #7: parse_blueprint_output() returns None due to indentation error
**Created:** 2026-02-06T02:49:45Z  
**Status:** Open  
**Labels:** None

### Description
After successful compilation, saving the draft fails with `'NoneType' object has no attribute 'get'` because `parse_blueprint_output()` returns `None` instead of the parsed assets dict.

### The Problem
In `bpui/parse_blocks.py`, lines 77-90 have an indentation bug where the asset construction code is indented under the error `raise`, making it unreachable dead code.

### Fix Location
`bpui/parse_blocks.py` lines 77-90

### Status
Confirmed working fix available - needs proper indentation inside the `with` block.

---

## Issue #6: Windows encoding error - read_text() missing utf-8 encoding
**Created:** 2026-02-06T02:49:09Z  
**Status:** Open  
**Labels:** None

### Description
On Windows, compilation fails with `'charmap' codec can't decode byte 0x9d` when reading blueprint/rules markdown files.

### The Problem
In `bpui/prompting.py`, five `.read_text()` calls (lines 18, 39, 80, 85, 208) don't specify encoding, defaulting to `cp1252` on Windows instead of UTF-8.

### Fix Location
`bpui/prompting.py` lines 18, 39, 80, 85, 208

### Additional Files to Audit
- `pack_io.py`
- `batch_state.py:130`
- `metadata.py:50`

### Status
Confirmed working fix available - add `encoding='utf-8'` to all `.read_text()` calls.

---

## Issue #5: Back button broken on Seed Generator screen
**Created:** 2026-02-06T00:59:32Z  
**Status:** Open  
**Labels:** None

### Description
The "← Back" button on the Seed Generator screen does nothing when clicked.

### The Problem
In `bpui/gui/seed_generator.py` line 224-228, `go_back()` uses `self.parent()` which returns the `QStackedWidget` instead of the `MainWindow`, so the navigation fails silently.

### Fix Location
`bpui/gui/seed_generator.py` lines 224-228

### Additional Screens to Check
- `validate.py`
- `compile.py`
- `batch.py`
- Other GUI screens that may have the same pattern

### Status
Confirmed working fix available - store direct reference to main_window in `__init__`.

---

## Issue #4: Settings save fails - Config.model property has no setter
**Created:** 2026-02-06T00:57:32Z  
**Status:** Open  
**Labels:** None

### Description
Saving settings in the GUI crashes with `AttributeError: property 'model' of 'Config' object has no setter`.

### The Problem
In `bpui/gui/dialogs.py` line 446, `save_settings()` tries to assign directly to the read-only `model` property instead of using the `Config.set()` method.

### Fix Location
`bpui/gui/dialogs.py` line 446

### Status
Confirmed working fix available - use `self.config.set("model", ...)` instead of direct assignment.

---

## Issue #3: pyproject.toml has wrong build backend
**Created:** 2026-02-06T00:39:09Z  
**Status:** Open  
**Labels:** None

### Description
`pyproject.toml` specifies an incorrect build backend, causing `pip install -e .` to fail with `BackendUnavailable: Cannot import 'setuptools.build_backend'`.

### The Problem
In `pyproject.toml` line 3, the build backend is set to `setuptools.build_backend` which doesn't exist. Should be `setuptools.build_meta`.

### Fix Location
`pyproject.toml` line 3

### Status
Confirmed working fix available - one-character fix: `backend` → `meta`.

---

## Priority Recommendations

### Critical (Blocks functionality)
1. **Issue #3** - Build system broken, prevents installation
2. **Issue #7** - Compilation fails to save drafts
3. **Issue #6** - Windows users cannot compile at all

### High (Major functionality broken)
4. **Issue #4** - Settings cannot be saved in GUI
5. **Issue #5** - Navigation broken in GUI

All bugs have confirmed fixes available and are ready to be implemented.