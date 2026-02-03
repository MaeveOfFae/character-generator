"""Drafts browser screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, ListView, ListItem


class DraftsScreen(Screen):
    """Browse saved drafts screen."""

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
                yield Button("⬅️  Back", id="back")

            yield Static("", id="status", classes="status")

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
