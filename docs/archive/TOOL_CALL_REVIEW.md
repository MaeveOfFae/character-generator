# Agent Tool Call System Review
**Date:** February 12, 2026  
**Reviewed Files:** `bpui/gui/agent_actions.py`, `bpui/gui/agent_chatbox.py`

## ✅ Strengths

1. **Comprehensive Error Handling** - Circuit breaker, retry logic, timeout protection all implemented
2. **17 Tools Covering Major Features** - Navigation, editing, compilation, seed generation, batch processing
3. **Robust Validation** - Pre-execution parameter validation against tool definitions
4. **Self-Recovery Capability** - LLM receives detailed error messages with suggestions
5. **Good Parameter Typing** - Proper use of enums for restricted values

## ⚠️ Issues Found

### 1. **Missing Screen Support in `get_screen_state`**
**Severity:** Medium  
**Location:** `agent_actions.py:_get_screen_state()`

The `navigate_to_screen` tool allows navigation to:
- `template_manager`
- `offspring`
- `similarity`

But `get_screen_state()` doesn't detect or extract information from these screens. It falls back to generic handling.

**Impact:** Agent can navigate to these screens but can't see what's on them.

**Recommendation:**
```python
# Add detection for missing screens
elif isinstance(current_screen, TemplateManagerScreen):
    screen_info["screen_name"] = "template_manager"
    # Extract template list, selected template, etc.

elif isinstance(current_screen, OffspringScreen):
    screen_info["screen_name"] = "offspring"
    # Extract parent characters, offspring settings, etc.

elif isinstance(current_screen, SimilarityScreen):
    screen_info["screen_name"] = "similarity"
    # Extract similarity results, search query, etc.
```

### 2. **Default Parameter Handling Inconsistency**
**Severity:** Low  
**Location:** Multiple tool definitions

Several tools specify `"default"` in their parameter definitions:
- `edit_current_asset`: `append` default False
- `compile_character`: `mode` default "Auto"
- `list_available_drafts`: `limit` default 20
- `generate_seeds`: `genres` and `count` have defaults

**Issue:** JSON Schema `"default"` is informational only - doesn't auto-fill missing params.

**Current Behavior:** Works because Python function signatures have defaults.

**Recommendation:** Either:
1. Remove `"default"` from tool definitions (misleading)
2. OR add default injection in `_validate_arguments()`:
```python
# In _validate_arguments, after checking required params:
for param_name, prop in properties.items():
    if param_name not in arguments and "default" in prop:
        arguments[param_name] = prop["default"]
```

### 3. **`export_character` Doesn't Use `name` Parameter**
**Severity:** Medium  
**Location:** `agent_actions.py:_export_character()`

Tool definition accepts optional `name` parameter, but implementation ignores it:
```python
def _export_character(self, name: Optional[str] = None) -> Dict[str, Any]:
    # ...
    review_widget.export_pack()  # <-- name not passed!
```

**Impact:** Agent can't specify export name.

**Recommendation:**
```python
def _export_character(self, name: Optional[str] = None) -> Dict[str, Any]:
    # ...
    if hasattr(review_widget, 'export_pack'):
        # Check if export_pack accepts name parameter
        import inspect
        sig = inspect.signature(review_widget.export_pack)
        if 'name' in sig.parameters and name:
            review_widget.export_pack(name=name)
        else:
            review_widget.export_pack()
```

### 4. **No Tool to Get Current Draft Metadata**
**Severity:** Low  
**Location:** Missing tool

Agent can list/search drafts but can't get metadata for the *currently open* draft in review mode.

**Use Case:** Agent needs to know:
- Current character name
- What model generated it
- Original seed
- Content mode
- Tags/genre

**Recommendation:** Add new tool:
```python
{
    "type": "function",
    "function": {
        "name": "get_current_draft_metadata",
        "description": "Get metadata for the currently open draft in review mode",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
```

### 5. **Tool Descriptions Could Be More Specific**
**Severity:** Low  
**Location:** Multiple tool definitions

Some descriptions lack detail about:
- Prerequisites (which screen must be active)
- Side effects (navigation happens automatically)
- Return value structure

**Examples:**
- `compile_character`: Doesn't mention it auto-navigates to compile screen
- `open_draft`: Doesn't mention it auto-navigates to review screen
- `get_asset_content`: Could specify it returns content in a `content` field

**Recommendation:** Enhance descriptions with prerequisites and behaviors:
```python
"description": "Start compiling a character from a seed. Automatically navigates to compile screen and starts generation. Returns immediately; use get_compile_status to check progress."
```

### 6. **Missing Useful Inspection Tools**
**Severity:** Low  
**Location:** Missing tools

Could benefit from:
- `get_current_character_name()` - Quick access to character name from sheet
- `get_compilation_history()` - Recently compiled characters
- `check_file_exists(path)` - Verify draft/file exists
- `get_app_config()` - Current LLM model, settings

### 7. **`start_batch_compilation` Missing Status Check**
**Severity:** Low  
**Location:** `agent_actions.py:_start_batch_compilation()`

Starts batch but provides no way to track progress or check if batch is already running.

**Recommendation:**
- Return batch job ID or status
- Add `get_batch_status()` tool

### 8. **Type Inconsistency in Error Returns**
**Severity:** Very Low  
**Location:** Multiple action methods

Some actions return extra fields inconsistently:
- `_get_asset_content()` returns `content` field
- `_list_available_drafts()` returns `drafts` and `total_available` fields
- Others only return `success` and `message`

**Impact:** LLM can't reliably parse structured data.

**Recommendation:** Standardize on:
```python
{
    "success": bool,
    "message": str,
    "data": {  # All structured data goes here
        "content": "...",
        "items": [...],
        "metadata": {...}
    },
    "error_type": str,  # Present only on failure
    "suggestion": str   # Present only on failure
}
```

## 🔧 Proposed Fixes Priority

### High Priority
1. ✅ **Already Fixed:** Timeout, retry, circuit breaker, error handling
2. Fix `export_character` to use name parameter (5 min)
3. Add screen state detection for template_manager/offspring/similarity (10 min)

### Medium Priority
4. Add `get_current_draft_metadata` tool (15 min)
5. Standardize return structure for all tools (20 min)
6. Enhance tool descriptions with prerequisites (10 min)

### Low Priority
7. Add default parameter injection in validation (10 min)
8. Add missing inspection tools (30 min per tool)
9. Add batch compilation status tracking (20 min)

## 📊 Coverage Analysis

| Screen | Navigation | State Inspection | Actions |
|--------|-----------|------------------|---------|
| Home | ✅ | ✅ (HomeWidget) | ✅ open_draft |
| Compile | ✅ | ✅ (CompileWidget) | ✅ compile_character, get_compile_status |
| Review | ✅ | ✅ (ReviewWidget) | ✅ edit, switch_tab, save, export, get_content |
| Batch | ✅ | ✅ (BatchScreen) | ✅ start_batch_compilation |
| Seed Generator | ✅ | ✅ (SeedGeneratorScreen) | ✅ generate_seeds, use_seed, get_seeds |
| Validate | ✅ | ✅ (ValidateScreen) | ✅ validate_character_pack |
| Template Manager | ✅ | ❌ Missing | ❌ No tools |
| Offspring | ✅ | ❌ Missing | ❌ No tools |
| Similarity | ✅ | ❌ Missing | ❌ No tools |

## 🎯 Recommendations Summary

1. **Complete screen coverage** - Add state inspection + actions for template_manager, offspring, similarity
2. **Fix export_character** - Pass name parameter through to implementation
3. **Add current draft metadata tool** - Essential for context-aware editing
4. **Standardize return structure** - Make LLM parsing predictable
5. **Enhance descriptions** - Document prerequisites and side effects
6. **Consider adding:**
   - Quick accessors (get character name, get model, etc.)
   - History tools (recent compilations, recent exports)
   - Batch status tracking
   - File existence checks

## ✨ Overall Assessment

**Grade: B+**

The tool system is well-implemented with excellent error handling and recovery mechanisms. The main gaps are:
- Incomplete coverage of newer screens (template_manager, offspring, similarity)
- Minor inconsistencies in parameter handling and return structures
- Missing some convenient accessor tools

The foundation is solid. The issues are polish/completeness rather than fundamental flaws.
