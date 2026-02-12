# Blueprint Editor and Template Builder Improvements

## Overview

The blueprint editor and template builder have been significantly enhanced to work seamlessly with the new organized blueprint structure and provide better user experience.

## New Features

### 1. Blueprint Browser (`blueprint_browser.py`)

A new dialog that allows browsing and selecting blueprints from the organized directory structure.

**Features:**
- Tree-based navigation of blueprint categories
- 📋 **System Blueprints** - Core system and orchestrator blueprints
- 📦 **Template Blueprints** - Template-specific blueprints organized by template
- 💡 **Example Blueprints** - Alternative and example blueprints
- Live preview of blueprint content
- Display of blueprint descriptions from frontmatter
- Relative path calculation for easy reference
- Double-click to select and close

**Usage:**
```python
from bpui.gui.blueprint_browser import BlueprintBrowserDialog

dialog = BlueprintBrowserDialog(parent, official_dir)
if dialog.exec():
    blueprint_name, blueprint_path = dialog.get_selected_blueprint()
```

### 2. Enhanced Asset Designer (`asset_designer.py`)

Updated to integrate with the blueprint browser for better blueprint selection.

**New Features:**
- **Browse Blueprints** option - Opens blueprint browser to select from organized structure
- Visual display of selected blueprint with relative path
- Proper handling of relative blueprint paths
- Support for selecting blueprints from system, template, or examples directories

**Blueprint Source Options:**
1. **Browse Blueprints** - Select from organized structure (NEW)
2. **Use Custom Blueprint** - Specify custom filename manually
3. **Create New Blueprint** - Design new blueprint later

### 3. Blueprint Editor Validation (`blueprint_editor.py`)

Added comprehensive validation to ensure blueprint quality before saving.

**Validation Checks:**
- ✓ Blueprint name is required
- ✓ Description is required
- ✓ Version major must be at least 1
- ✓ Blueprint content is required
- ✓ Blueprint should define an agent role ("agent" or "you are")
- ✓ Blueprint content should be sufficient length
- ✓ No template placeholders left in content
- ✓ Blueprint should include section headers for organization

**Behavior:**
- Validates before saving
- Shows all validation errors
- Allows saving despite errors (with confirmation)
- Helps maintain blueprint quality standards

### 4. Updated Template Manager (`templates.py`)

Enhanced to support the new organized blueprint structure.

**Blueprint Resolution Order:**
1. Template's `assets/` directory
2. Relative path resolution (e.g., `../../system/system_prompt.md`)
3. Template-specific blueprint directories (`blueprints/templates/*/`)
4. System directory (`blueprints/system/`)
5. Examples directory (`blueprints/examples/`)
6. Direct path from blueprints root (`blueprints/`)

**Official Template:**
- Updated to reference blueprints from new structure
- Uses relative paths for system blueprints
- Points to `example_minimal` as base template

## Integration with New Blueprint Structure

The improvements are designed to work seamlessly with the reorganized blueprint structure:

```
blueprints/
├── system/          # 🔧 System Blueprints
├── templates/       # 📦 Template Blueprints
│   ├── example_image_only/
│   ├── example_music_only/
│   └── example_minimal/
└── examples/        # 💡 Example Blueprints
```

## User Workflow Improvements

### Before
- Had to know exact blueprint filenames
- Limited to blueprints in flat directory
- No preview of blueprint content
- No validation of blueprint structure

### After
- Browse blueprints by category
- Preview blueprint content before selection
- See relative paths for easy reference
- Comprehensive validation before saving
- Better organization and discoverability

## Code Quality Improvements

1. **Type Hints** - Added proper type annotations throughout
2. **Error Handling** - Robust error handling with user-friendly messages
3. **Documentation** - Comprehensive docstrings for all methods
4. **UI Consistency** - Consistent styling and layout across dialogs
5. **Path Handling** - Proper relative/absolute path resolution

## Future Enhancements

Potential future improvements:
- [ ] Dependency visualization (graph view)
- [ ] Blueprint templates/scaffolding
- [ ] Search/filter functionality in blueprint browser
- [ ] Blueprint version comparison
- [ ] Import/export of blueprints
- [ ] Blueprint testing/validation framework

## Testing

To test the improvements:

1. **Blueprint Browser:**
   - Run the application
   - Open template wizard
   - Add new asset
   - Click "Browse Blueprints"
   - Navigate through system, template, and example blueprints
   - Preview different blueprints

2. **Asset Designer:**
   - Select "Browse Blueprints" option
   - Browse and select a blueprint
   - Verify relative path is displayed correctly

3. **Blueprint Editor:**
   - Create/edit a blueprint
   - Try saving with missing fields
   - Observe validation warnings
   - Fix issues and save successfully

## Files Modified/Created

### New Files
- `bpui/gui/blueprint_browser.py` - Blueprint browsing dialog

### Modified Files
- `bpui/gui/asset_designer.py` - Added blueprint browser integration
- `bpui/gui/blueprint_editor.py` - Added validation logic
- `bpui/templates.py` - Updated blueprint resolution for new structure
- `bpui/gui/template_wizard.py` - References updated dialogs

### Documentation
- `bpui/gui/IMPROVEMENTS.md` - This file