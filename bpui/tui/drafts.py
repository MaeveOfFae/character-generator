"""Drafts browser screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, ListView, ListItem, Footer


class DraftsScreen(Screen):
    """Browse saved drafts screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("enter", "open_draft", "Open"),
        ("d", "delete_draft", "Delete"),
    ]

    CSS = """
    DraftsScreen {
        layout: vertical;
    }

    #drafts-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    .title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #drafts-list {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }

    .button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
    }

    .button-row Button {
        width: 1fr;
        margin-right: 1;
    }

    .status {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, config):
        """Initialize drafts screen."""
        super().__init__()
        self.config = config
        self.drafts = []

    def compose(self) -> ComposeResult:
        """Compose drafts screen."""
        with Container(id="drafts-container"):
            yield Static("📁 Saved Drafts", classes="title")
            yield ListView(id="drafts-list")

            with Vertical(classes="button-row"):
                yield Button("🔄 Refresh", id="refresh", variant="primary")
                yield Button("⬅️  [Q] Back", id="back")

            yield Static("", id="status", classes="status")
            yield Footer()

    async def on_mount(self) -> None:
        """Handle mount - load drafts."""
        await self.load_drafts()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "refresh":
            await self.load_drafts()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle draft selection."""
        if event.item and self.drafts:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.drafts):
                draft_dir = self.drafts[idx]
                await self.open_draft(draft_dir)

    async def load_drafts(self) -> None:
        """Load drafts list."""
        from ..pack_io import list_drafts

        status = self.query_one("#status", Static)
        drafts_list = self.query_one("#drafts-list", ListView)

        status.update("Loading drafts...")

        try:
            self.drafts = list_drafts()
            await drafts_list.clear()

            if not self.drafts:
                await drafts_list.append(ListItem(Static("[No drafts found]")))
                status.update("No drafts found")
            else:
                for draft_dir in self.drafts:
                    await drafts_list.append(ListItem(Static(draft_dir.name)))
                status.update(f"{len(self.drafts)} drafts found")

        except Exception as e:
            status.update(f"Error loading drafts: {e}")

    async def open_draft(self, draft_dir) -> None:
        """Open a draft in review screen."""
        from ..pack_io import load_draft
        from .review import ReviewScreen

        try:
            assets = load_draft(draft_dir)
            self.app.push_screen(ReviewScreen(self.config, draft_dir, assets))
        except Exception as e:
            status = self.query_one("#status", Static)
            status.update(f"Error loading draft: {e}")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        from .home import HomeScreen
        self.app.switch_screen(HomeScreen(self.config))
    
    def action_open_draft(self) -> None:
        """Open selected draft (Enter key)."""
        drafts_list = self.query_one("#drafts-list", ListView)
        if drafts_list.index is not None and self.drafts:
            idx = drafts_list.index
            if 0 <= idx < len(self.drafts):
                draft_dir = self.drafts[idx]
                self.run_worker(lambda: self.open_draft(draft_dir))
    
    def action_delete_draft(self) -> None:
        """Delete selected draft (D key)."""
        drafts_list = self.query_one("#drafts-list", ListView)
        
        if drafts_list.index is None or not self.drafts:
            return
        
        idx = drafts_list.index
        if not 0 <= idx < len(self.drafts):
            return
        
        draft_dir = self.drafts[idx]
        
        # Show confirmation dialog
        self.app.push_screen(DeleteConfirmScreen(draft_dir.name, self._confirm_delete))
    
    def _confirm_delete(self, confirmed: bool) -> None:
        """Handle delete confirmation."""
        if not confirmed:
            return
        
        drafts_list = self.query_one("#drafts-list", ListView)
        status = self.query_one("#status", Static)
        
        if drafts_list.index is None or not self.drafts:
            return
        
        idx = drafts_list.index
        if not 0 <= idx < len(self.drafts):
            return
        
        draft_dir = self.drafts[idx]
        
        try:
            from ..pack_io import delete_draft
            delete_draft(draft_dir)
            status.update(f"✓ Deleted: {draft_dir.name}")
            # Reload drafts list
            self.run_worker(self.load_drafts)
        except Exception as e:
            status.update(f"✗ Error deleting draft: {e}")


class DeleteConfirmScreen(Screen):
    """Confirmation dialog for deleting drafts."""
    
    BINDINGS = [
        ("y", "confirm", "Yes, delete"),
        ("n,escape,q", "cancel", "No, cancel"),
    ]
    
    CSS = """
    DeleteConfirmScreen {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 60;
        height: 12;
        border: solid $warning;
        background: $panel;
        padding: 1;
    }
    
    #message {
        content-align: center middle;
        margin-bottom: 2;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    """
    
    def __init__(self, draft_name: str, callback):
        """Initialize confirmation dialog."""
        super().__init__()
        self.draft_name = draft_name
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        """Compose confirmation dialog."""
        with Vertical(id="dialog"):
            yield Static(f"Delete draft:\n\n  {self.draft_name}\n\nThis cannot be undone!", id="message")
            with Container(id="buttons"):
                yield Button("Yes, Delete", id="confirm", variant="error")
                yield Button("Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm":
            self.app.pop_screen()
            self.callback(True)
        else:
            self.app.pop_screen()
            self.callback(False)
    
    def action_confirm(self) -> None:
        """Confirm deletion (Y key)."""
        self.app.pop_screen()
        self.callback(True)
    
    def action_cancel(self) -> None:
        """Cancel deletion (N/Escape/Q keys)."""
        self.app.pop_screen()
        self.callback(False)
