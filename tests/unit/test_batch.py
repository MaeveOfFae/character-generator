"""Tests for batch compilation."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from textual.widgets import Button, Static, Input, Select, ProgressBar

from bpui.tui.batch import BatchScreen
from bpui.core.config import Config


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config."""
    config_file = tmp_path / ".bpui.toml"
    config = Config(config_file)
    config._data["model"] = "test/model"
    config._data["engine"] = "litellm"
    return config


@pytest.fixture
def sample_seeds_file(tmp_path):
    """Create a sample seeds file."""
    seeds_file = tmp_path / "test_seeds.txt"
    seeds_file.write_text(
        "A cyberpunk detective with telekinetic powers\n"
        "A medieval blacksmith haunted by their past\n"
        "A space pirate with a conscience\n"
    )
    return seeds_file


@pytest.mark.asyncio
async def test_initial_state(temp_config):
    """Test batch screen initial state."""
    screen = BatchScreen(temp_config)
    
    assert screen.config == temp_config
    assert screen.seeds == []
    assert screen.current_index == 0
    assert screen.failed_seeds == []
    assert screen.batch_running is False


@pytest.mark.asyncio
async def test_load_seeds_success(temp_config, sample_seeds_file):
    """Test loading seeds from file."""
    screen = BatchScreen(temp_config)
    
    # Mock UI components
    seed_file_input = Mock(spec=Input)
    seed_file_input.value = str(sample_seeds_file)
    
    log = Mock()
    status = Mock(spec=Static)
    start_button = Mock(spec=Button)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#seed-file":
            return seed_file_input
        elif selector == "#log":
            return log
        elif selector == "#status":
            return status
        elif selector == "#start":
            return start_button
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    await screen.load_seeds()
    
    assert len(screen.seeds) == 3
    assert screen.seeds[0] == "A cyberpunk detective with telekinetic powers"
    assert start_button.disabled is False
    log.write.assert_called()


@pytest.mark.asyncio
async def test_load_seeds_file_not_found(temp_config):
    """Test loading from non-existent file."""
    screen = BatchScreen(temp_config)
    
    seed_file_input = Mock(spec=Input)
    seed_file_input.value = "/nonexistent/file.txt"
    
    log = Mock()
    status = Mock(spec=Static)
    start_button = Mock(spec=Button)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#seed-file":
            return seed_file_input
        elif selector == "#log":
            return log
        elif selector == "#status":
            return status
        elif selector == "#start":
            return start_button
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    await screen.load_seeds()
    
    assert len(screen.seeds) == 0
    assert start_button.disabled is not False
    assert any("not found" in str(call) for call in log.write.call_args_list)


@pytest.mark.asyncio
async def test_load_seeds_empty_file(temp_config, tmp_path):
    """Test loading from empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("\n\n  \n")
    
    screen = BatchScreen(temp_config)
    
    seed_file_input = Mock(spec=Input)
    seed_file_input.value = str(empty_file)
    
    log = Mock()
    status = Mock(spec=Static)
    start_button = Mock(spec=Button)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#seed-file":
            return seed_file_input
        elif selector == "#log":
            return log
        elif selector == "#status":
            return status
        elif selector == "#start":
            return start_button
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    await screen.load_seeds()
    
    assert len(screen.seeds) == 0
    assert any("No seeds" in str(call) for call in log.write.call_args_list)


@pytest.mark.asyncio
async def test_button_pressed_home_while_running(temp_config):
    """Test home button while batch is running."""
    screen = BatchScreen(temp_config)
    screen.batch_running = True
    
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    # Create mock app first to set context
    mock_app = Mock()
    screen._app = mock_app  # type: ignore
    
    mock_button = Mock(spec=Button)
    mock_button.id = "home"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    # Should not switch screens
    assert not mock_app.switch_screen.called
    status.update.assert_called()


@pytest.mark.asyncio
async def test_button_pressed_load(temp_config):
    """Test load button."""
    screen = BatchScreen(temp_config)
    screen.load_seeds = AsyncMock()
    
    mock_button = Mock(spec=Button)
    mock_button.id = "load"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    screen.load_seeds.assert_called_once()


@pytest.mark.asyncio
async def test_button_pressed_start(temp_config):
    """Test start button."""
    screen = BatchScreen(temp_config)
    screen.start_batch = AsyncMock()
    
    mock_button = Mock(spec=Button)
    mock_button.id = "start"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    screen.start_batch.assert_called_once()


@pytest.mark.asyncio
async def test_button_pressed_cancel(temp_config):
    """Test cancel button."""
    screen = BatchScreen(temp_config)
    screen.cancel_batch = AsyncMock()
    
    mock_button = Mock(spec=Button)
    mock_button.id = "cancel"
    
    mock_event = Mock()
    mock_event.button = mock_button
    
    await screen.on_button_pressed(mock_event)
    
    screen.cancel_batch.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_batch(temp_config):
    """Test cancelling batch operation."""
    screen = BatchScreen(temp_config)
    screen.batch_running = True
    
    cancel_button = Mock(spec=Button)
    status = Mock(spec=Static)
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#cancel":
            return cancel_button
        elif selector == "#status":
            return status
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    
    await screen.cancel_batch()
    
    assert screen.batch_running is False
    assert cancel_button.disabled is True
    status.update.assert_called_with("Cancelling...")


@pytest.mark.asyncio
async def test_start_batch_no_seeds(temp_config):
    """Test starting batch with no seeds."""
    screen = BatchScreen(temp_config)
    screen.seeds = []
    
    await screen.start_batch()
    
    # Should do nothing
    assert screen.batch_running is False


@pytest.mark.asyncio
async def test_start_batch_with_seeds(temp_config):
    """Test starting batch with seeds."""
    screen = BatchScreen(temp_config)
    screen.seeds = ["Test seed 1", "Test seed 2"]
    
    # Mock UI components
    load_button = Mock(spec=Button)
    start_button = Mock(spec=Button)
    cancel_button = Mock(spec=Button)
    progress_bar = Mock(spec=ProgressBar)
    log = Mock()
    
    def mock_query_one(selector, expect_type=None):  # type: ignore
        if selector == "#load":
            return load_button
        elif selector == "#start":
            return start_button
        elif selector == "#cancel":
            return cancel_button
        elif selector == "#progress-bar":
            return progress_bar
        elif selector == "#log":
            return log
        return Mock()
    
    screen.query_one = mock_query_one  # type: ignore
    screen.run_worker = Mock()
    
    await screen.start_batch()
    
    assert screen.batch_running is True
    assert screen.current_index == 0
    assert len(screen.failed_seeds) == 0
    assert load_button.disabled is True
    assert start_button.disabled is True
    assert cancel_button.disabled is False
    progress_bar.update.assert_called()
    screen.run_worker.assert_called()
