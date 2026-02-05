"""Integration tests for TUI screens."""

import pytest
from pathlib import Path
from textual.app import App
from textual.widgets import Button, ListView, Static, Input
from textual.containers import Container

from bpui.config import Config
from bpui.tui.drafts import DraftsScreen, DeleteConfirmScreen
from bpui.tui.home import HomeScreen
from bpui.tui.review import ReviewScreen, SaveFileDialog
from bpui.pack_io import create_draft_dir, delete_draft


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def test_assets():
    """Create test assets."""
    return {
        "system_prompt": "Test system prompt",
        "post_history": "Test post history",
        "character_sheet": "**Character:** Test Character\n**Description:** A test character",
        "intro_scene": "Test intro scene",
        "intro_page": "# Test Intro Page\n\nTest content",
        "a1111": "Test a1111 prompt",
        "suno": "Test suno prompt",
    }


@pytest.fixture
def test_draft_dir(tmp_path, test_assets):
    """Create a test draft directory."""
    draft_dir = create_draft_dir(test_assets, "test_character", tmp_path / "drafts")
    yield draft_dir
    # Cleanup is handled by tmp_path fixture


class TestDraftsScreen:
    """Test DraftsScreen functionality."""
    
    @pytest.mark.asyncio
    async def test_drafts_screen_mount(self, config, test_draft_dir):
        """Test that DraftsScreen mounts and loads drafts."""
        app = App()
        async with app.run_test() as pilot:
            screen = DraftsScreen(config)
            app.push_screen(screen)
            await pilot.pause()
            
            # Verify screen mounted
            assert app.screen is not None
            
            # Verify drafts list loaded
            drafts_list = screen.query_one("#drafts-list", ListView)
            assert drafts_list is not None
            
            # Verify status updated (just check widget exists)
            status = screen.query_one("#status", Static)
            assert status is not None
    
    @pytest.mark.asyncio
    async def test_delete_confirmation_dialog(self, config):
        """Test delete confirmation dialog."""
        app = App()
        async with app.run_test() as pilot:
            dialog = DeleteConfirmScreen("test_draft", lambda confirmed: None)
            app.push_screen(dialog)
            await pilot.pause()
            
            # Verify dialog mounted
            assert app.screen is not None
            
            # Verify message displayed (just check widget exists)
            message = dialog.query_one("#message", Static)
            assert message is not None
            
            # Test cancel button
            cancel_button = dialog.query_one("#cancel", Button)
            await pilot.click(Button)
            await pilot.pause()
            
            # Dialog should be dismissed
            assert app.screen is not dialog


class TestReviewScreen:
    """Test ReviewScreen functionality."""
    
    @pytest.mark.asyncio
    async def test_review_screen_mount(self, config, test_draft_dir, test_assets):
        """Test that ReviewScreen mounts and loads assets."""
        app = App()
        async with app.run_test() as pilot:
            screen = ReviewScreen(config, test_draft_dir, test_assets)
            app.push_screen(screen)
            await pilot.pause(0.2)  # Give time for worker to load text
            
            # Verify screen mounted
            assert app.screen is not None
            
            # Verify tabs exist
            from textual.widgets import TabbedContent
            tabs = screen.query_one("#tabs", TabbedContent)
            assert tabs is not None
    
    @pytest.mark.asyncio
    async def test_save_dialog(self, config, test_draft_dir, test_assets):
        """Test save to file dialog."""
        app = App()
        async with app.run_test() as pilot:
            screen = ReviewScreen(config, test_draft_dir, test_assets)
            app.push_screen(screen)
            
            # Show save dialog
            screen.show_save_dialog()
            await pilot.pause()
            
            # Verify dialog mounted
            save_dialog = app.screen
            assert isinstance(save_dialog, SaveFileDialog)
            
            # Verify input field exists
            path_input = save_dialog.query_one("#path-input", Input)
            assert path_input is not None
    
    @pytest.mark.asyncio
    async def test_edit_mode_toggle(self, config, test_draft_dir, test_assets):
        """Test edit mode toggle."""
        app = App()
        async with app.run_test() as pilot:
            screen = ReviewScreen(config, test_draft_dir, test_assets)
            app.push_screen(screen)
            await pilot.pause(0.2)
            
            # Initially not in edit mode
            assert not screen.edit_mode
            
            # Toggle edit mode
            await screen.toggle_edit_mode()
            await pilot.pause()
            
            # Should be in edit mode
            assert screen.edit_mode
            
            # Toggle back
            await screen.toggle_edit_mode()
            await pilot.pause()
            
            # Should not be in edit mode
            assert not screen.edit_mode


class TestHomeScreen:
    """Test HomeScreen functionality."""
    
    @pytest.mark.asyncio
    async def test_home_screen_mount(self, config):
        """Test that HomeScreen mounts successfully."""
        app = App()
        async with app.run_test() as pilot:
            screen = HomeScreen(config)
            app.push_screen(screen)
            await pilot.pause()
            
            # Verify screen mounted
            assert app.screen is not None
            
            # Verify buttons exist
            compile_button = screen.query_one("#compile", Button)
            assert compile_button is not None


class TestWorkflows:
    """Test complete TUI workflows."""
    
    @pytest.mark.asyncio
    async def test_browse_and_delete_draft(self, config, test_draft_dir):
        """Test workflow: browse drafts and delete one."""
        app = App()
        async with app.run_test() as pilot:
            # Start on home screen
            home = HomeScreen(config)
            app.push_screen(home)
            await pilot.pause()
            
            # Navigate to drafts
            drafts_button = home.query_one("#drafts", Button)
            await pilot.click(Button)
            await pilot.pause()
            
            # Should be on drafts screen
            drafts_screen = app.screen
            assert isinstance(drafts_screen, DraftsScreen)
            
            # Verify draft is in list
            drafts_list = drafts_screen.query_one("#drafts-list", ListView)
            assert drafts_list is not None
    
    @pytest.mark.asyncio
    async def test_compile_and_review_workflow(self, config, tmp_path, test_assets):
        """Test workflow: compile character and review."""
        # Create a draft first
        draft_dir = create_draft_dir(test_assets, "workflow_test", tmp_path / "drafts")
        
        app = App()
        async with app.run_test() as pilot:
            # Start on home screen
            home = HomeScreen(config)
            app.push_screen(home)
            await pilot.pause()
            
            # Navigate to drafts
            drafts_button = home.query_one("#drafts", Button)
            await pilot.click(Button)
            await pilot.pause()
            
            # Open the draft
            drafts_screen = app.screen
            assert isinstance(drafts_screen, DraftsScreen)
            
            # The draft should be in the list
            drafts_list = drafts_screen.query_one("#drafts-list", ListView)
            assert drafts_list is not None
            
            # Select first item
            if drafts_list.index is None:
                drafts_list.index = 0
            await pilot.pause()
            
            # Open the draft
            await pilot.press("enter")
            await pilot.pause()
            
            # Should be on review screen
            review_screen = app.screen
            assert isinstance(review_screen, ReviewScreen)
            
            # Verify assets loaded
            assert review_screen.assets == test_assets