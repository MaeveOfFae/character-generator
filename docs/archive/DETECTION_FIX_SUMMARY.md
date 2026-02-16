# Detection Fix Summary

## Problem
The `get_screen_state()` method in `bpui/gui/agent_actions.py` was failing to properly detect the state of the SimilarityWidget screen, causing issues with the agent's ability to understand what's happening on that screen.

## Root Cause
The detection code was attempting to access attributes that don't exist on the `SimilarityWidget` class:

**Incorrect attributes being accessed:**
- `selected_char1` - doesn't exist
- `selected_char2` - doesn't exist  
- `comparison_mode` - doesn't exist
- `analysis_running` - doesn't exist

**Actual attributes available:**
- `char1_combo` (QComboBox) - for first character selection
- `char2_combo` (QComboBox) - for second character selection
- `compare_all_checkbox` (QCheckBox) - determines batch mode
- `cluster_checkbox` (QCheckBox) - determines cluster mode
- `compare_btn` (QPushButton) - use `isEnabled()` to check if analysis is running
- `use_llm_checkbox` (QCheckBox) - LLM analysis setting
- `threshold_spinbox` (QSpinBox) - cluster threshold when in cluster mode

## Solution
Updated the `SimilarityWidget` detection code in `_get_screen_state()` to:

1. **Get selected characters from combo boxes:**
   ```python
   screen_info["elements"]["character1"] = current_screen.char1_combo.currentText()
   screen_info["elements"]["character2"] = current_screen.char2_combo.currentText()
   ```

2. **Determine comparison mode from checkboxes:**
   ```python
   if is_cluster:
       mode = "cluster"
   elif is_batch:
       mode = "batch_all_pairs"
   else:
       mode = "single_pair"
   ```

3. **Check if analysis is running via button state:**
   ```python
   is_analyzing = not current_screen.compare_btn.isEnabled()
   ```

4. **Add LLM analysis setting and cluster threshold:**
   ```python
   screen_info["elements"]["use_llm_analysis"] = current_screen.use_llm_checkbox.isChecked()
   screen_info["elements"]["cluster_threshold"] = f"{current_screen.threshold_spinbox.value()}%"
   ```

## Affected Screens
- ✅ **TemplateManagerScreen** - Detection already correct (has `selected_template`, `templates`, `templates_list`)
- ✅ **OffspringWidget** - Detection already correct (has `parent1_name`, `parent2_name`, `generation_thread`)
- ✅ **SimilarityWidget** - **FIXED** - Now properly detects state using correct attributes

## Impact
The agent can now:
- See which characters are selected for comparison
- Determine the current comparison mode (single pair, batch all pairs, or cluster)
- Check if an analysis is currently running
- Access results preview when available
- See LLM analysis settings and cluster thresholds

## Testing
Run the agent chatbox and navigate to the Similarity screen. The agent should now be able to:
```python
{
  "screen_name": "similarity",
  "elements": {
    "character1": "character_a",
    "character2": "character_b",
    "comparison_mode": "single_pair",
    "is_analyzing": false,
    "has_results": false,
    "use_llm_analysis": false
  }
}
```

## Files Modified
- `bpui/gui/agent_actions.py` - Updated `_get_screen_state()` method