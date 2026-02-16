"""Tests for Review screen edit mode."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from textual.widgets import Button, TextArea, Static

from bpui.tui.review import ReviewScreen
from bpui.core.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config."""
    config_file = tmp_path / ".bpui.toml"
    config = Config(config_file)
    config._data["model"] = "test/model"
    return config


@pytest.fixture
def sample_assets():
    """Sample assets for testing."""
    return {
        "system_prompt": "You are a test character.",
        "post_history": "The relationship is established.",
        "character_sheet": "name: Test Character\nage: 25",
        "intro_scene": "A test scene.",
        "intro_page": "# Test Page",
        "a1111": "[Control]\nTest prompt",
        "suno": "[Control]\nTest song",
    }


@pytest.fixture
def temp_draft_dir(tmp_path):
    """Create a temporary draft directory."""
    draft_dir = tmp_path / "test_draft"
    draft_dir.mkdir()
    
    # Create asset files
    (draft_dir / "system_prompt.txt").write_text("Original content")
    (draft_dir / "post_history.txt").write_text("Original history")
    (draft_dir / "character_sheet.txt").write_text("name: Original\nage: 30")
    (draft_dir / "intro_scene.txt").write_text("Original scene")
    (draft_dir / "intro_page.md").write_text("# Original")
    (draft_dir / "a1111_prompt.txt").write_text("Original a1111")
    (draft_dir / "suno_prompt.txt").write_text("Original suno")
    
    return draft_dir


@pytest.mark.asyncio
async def test_initial_state(temp_config, sample_assets, temp_draft_dir):
    """Test review screen initial state."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    
    assert screen.edit_mode is False
    assert len(screen.dirty_assets) == 0
    assert screen.config == temp_config
    assert screen.draft_dir == temp_draft_dir
    assert screen.assets == sample_assets


@pytest.mark.asyncio
async def test_toggle_edit_mode_on(temp_config, sample_assets, temp_draft_dir):
    """Test toggling edit mode on."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    
    # Mock the UI components
    screen.query_one = Mock()
    
    toggle_button = Mock(spec=Button)
    save_button = Mock(spec=Button)
    status = Mock(spec=Static)
    text_areas = [Mock(spec=TextArea) for _ in range(7)]
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#toggle_edit":
            return toggle_button
        elif selector == "#save":
            return save_button
        elif selector == "#status":
            return status
        elif "area" in selector:
            return text_areas.pop(0)
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Toggle to edit mode
    await screen.toggle_edit_mode()
    
    assert screen.edit_mode is True
    assert toggle_button.label == "👁️  View Mode"
    assert toggle_button.variant == "warning"


@pytest.mark.asyncio
async def test_toggle_edit_mode_off(temp_config, sample_assets, temp_draft_dir):
    """Test toggling edit mode off."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.edit_mode = True  # Start in edit mode
    
    # Mock the UI components
    screen.query_one = Mock()
    
    toggle_button = Mock(spec=Button)
    save_button = Mock(spec=Button)
    status = Mock(spec=Static)
    text_areas = [Mock(spec=TextArea) for _ in range(7)]
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#toggle_edit":
            return toggle_button
        elif selector == "#save":
            return save_button
        elif selector == "#status":
            return status
        elif "area" in selector:
            return text_areas.pop(0)
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Toggle to view mode
    await screen.toggle_edit_mode()
    
    assert screen.edit_mode is False
    assert toggle_button.label == "✏️  Edit Mode"
    assert toggle_button.variant == "default"


@pytest.mark.asyncio
async def test_on_text_area_changed_marks_dirty(temp_config, sample_assets, temp_draft_dir):
    """Test that text area changes mark assets as dirty."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.edit_mode = True
    
    # Mock components
    save_button = Mock(spec=Button)
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#save":
            return save_button
        elif selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Create a mock text area change event
    mock_text_area = Mock(spec=TextArea)
    mock_text_area.id = "system_prompt_area"
    mock_text_area.text = "Modified content"
    
    mock_event = Mock()
    mock_event.text_area = mock_text_area
    
    # Trigger change handler
    await screen.on_text_area_changed(mock_event)
    
    assert "system_prompt" in screen.dirty_assets
    assert save_button.disabled is False


@pytest.mark.asyncio
async def test_on_text_area_changed_ignores_in_view_mode(temp_config, sample_assets, temp_draft_dir):
    """Test that text area changes are ignored in view mode."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.edit_mode = False
    
    mock_text_area = Mock(spec=TextArea)
    mock_text_area.id = "system_prompt_area"
    mock_text_area.text = "Modified content"
    
    mock_event = Mock()
    mock_event.text_area = mock_text_area
    
    await screen.on_text_area_changed(mock_event)
    
    assert len(screen.dirty_assets) == 0


@pytest.mark.asyncio
async def test_save_changes_writes_files(temp_config, sample_assets, temp_draft_dir):
    """Test that save_changes writes modified files."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.edit_mode = True
    screen.dirty_assets.add("system_prompt")
    screen.dirty_assets.add("character_sheet")
    
    # Mock components
    status = Mock(spec=Static)
    validation_log = Mock()
    save_button = Mock(spec=Button)
    
    # Mock text areas with modified content
    system_prompt_area = Mock(spec=TextArea)
    system_prompt_area.text = "Modified system prompt"
    
    character_sheet_area = Mock(spec=TextArea)
    character_sheet_area.text = "name: Modified\nage: 99"
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#status":
            return status
        elif selector == "#validation-log":
            return validation_log
        elif selector == "#save":
            return save_button
        elif selector == "#system_prompt_area":
            return system_prompt_area
        elif selector == "#character_sheet_area":
            return character_sheet_area
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Mock validate_pack to avoid actual validation
    screen.validate_pack = AsyncMock()
    
    # Save changes
    await screen.save_changes()
    
    # Check that dirty assets were cleared
    assert len(screen.dirty_assets) == 0
    
    # Check that files were written
    assert (temp_draft_dir / "system_prompt.txt").read_text() == "Modified system prompt"
    assert (temp_draft_dir / "character_sheet.txt").read_text() == "name: Modified\nage: 99"
    
    # Check that save button was disabled
    assert save_button.disabled is True


@pytest.mark.asyncio
async def test_save_changes_no_changes(temp_config, sample_assets, temp_draft_dir):
    """Test save_changes when there are no changes."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    await screen.save_changes()
    
    status.update.assert_called_with("✓ No changes to save")


@pytest.mark.asyncio
async def test_save_changes_error_handling(temp_config, sample_assets, temp_draft_dir):
    """Test save_changes error handling."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.dirty_assets.add("system_prompt")
    
    status = Mock(spec=Static)
    validation_log = Mock()
    
    # Mock text area that will raise an error
    system_prompt_area = Mock(spec=TextArea)
    system_prompt_area.text = "Modified content"
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#status":
            return status
        elif selector == "#validation-log":
            return validation_log
        elif selector == "#system_prompt_area":
            return system_prompt_area
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Make the draft_dir non-writable by using a non-existent path
    screen.draft_dir = Path("/nonexistent/path")
    
    await screen.save_changes()
    
    # Check error was reported
    assert status.add_class.called
    assert any("error" in str(call) for call in status.add_class.call_args_list)


@pytest.mark.asyncio
async def test_button_pressed_home_with_dirty_assets(temp_config, sample_assets, temp_draft_dir):
    """Test that navigating home with unsaved changes shows warning."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.dirty_assets.add("system_prompt")
    
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Mock the app using patch
    with patch.object(screen, '_app', create=True) as mock_app:
        mock_button = Mock(spec=Button)
        mock_button.id = "home"
        
        mock_event = Mock()
        mock_event.button = mock_button
        
        await screen.on_button_pressed(mock_event)
        
        # Should not switch screens
        assert not mock_app.switch_screen.called
        
        # Should show warning
        status.update.assert_called()
        assert "unsaved" in status.update.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_button_pressed_toggle_edit(temp_config, sample_assets, temp_draft_dir):
    """Test toggle edit button."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.toggle_edit_mode = AsyncMock()
    
    mock_button = Mock(spec=Button)
    mock_button.id = "toggle_edit"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    screen.toggle_edit_mode.assert_called_once()


@pytest.mark.asyncio
async def test_button_pressed_save(temp_config, sample_assets, temp_draft_dir):
    """Test save button."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.save_changes = AsyncMock()
    
    mock_button = Mock(spec=Button)
    mock_button.id = "save"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    screen.save_changes.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_assets_dirty_tracking(temp_config, sample_assets, temp_draft_dir):
    """Test tracking multiple dirty assets."""
    screen = ReviewScreen(temp_config, temp_draft_dir, sample_assets)
    screen.edit_mode = True
    
    save_button = Mock(spec=Button)
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#save":
            return save_button
        elif selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Simulate changes to multiple assets
    for asset_id in ["system_prompt_area", "character_sheet_area", "intro_scene_area"]:
        mock_text_area = Mock(spec=TextArea)
        mock_text_area.id = asset_id
        mock_text_area.text = "Modified"
        
        mock_event = Mock()
        mock_event.text_area = mock_text_area
        
        await screen.on_text_area_changed(mock_event)
    
    assert len(screen.dirty_assets) == 3
    assert "system_prompt" in screen.dirty_assets
    assert "character_sheet" in screen.dirty_assets
    assert "intro_scene" in screen.dirty_assets
