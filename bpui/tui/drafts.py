"""Drafts browser screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, ListView, ListItem, Footer, Input, Select


class DraftsScreen(Screen):
    """Browse saved drafts screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("enter", "open_draft", "Open"),
        ("d", "delete_draft", "Delete"),
        ("f", "focus_search", "Search"),
        ("r", "toggle_favorite_filter", "Toggle Favorites"),
    ]

    def __init__(self, config):
        """Initialize drafts screen."""
        super().__init__()
        self.config = config
        self.all_drafts = []  # All drafts
        self.filtered_drafts = []  # Currently filtered drafts
        self.favorite_filter = False
        self.current_search = ""
        self.current_genre = ""
        self.current_sort = "newest"

    def compose(self) -> ComposeResult:
        """Compose drafts screen."""
        with Container(id="drafts-container"):
            yield Static("📁 Saved Drafts", classes="title")
            
            with Horizontal(id="search-container"):
                yield Input(placeholder="🔍 Search by name, character, or notes... (F)", id="search-input")
                yield Select(
                    [(genre, genre) for genre in ["All Genres", "Fantasy", "Sci-Fi", "Modern", "Historical", "Horror", "Romance"]],
                    id="genre-select",
                    value="All Genres",
                    allow_blank=False
                )
                yield Select(
                    [("Newest First", "newest"), ("Oldest First", "oldest"), ("Name A-Z", "name_asc"), ("Name Z-A", "name_desc")],
                    id="sort-select",
                    value="newest",
                    allow_blank=False
                )
            
            yield Static("", id="filter-info", classes="status")
            yield ListView(id="drafts-list")

            with Vertical(classes="button-row"):
                yield Button("⭐ Favorites Only [R]", id="favorites-toggle", variant="default")
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
        elif event.button.id == "favorites-toggle":
            self.action_toggle_favorite_filter()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input change."""
        if event.input.id == "search-input":
            self.current_search = event.value
            await self.apply_filters()

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "genre-select":
            genre = event.value
            self.current_genre = "" if genre == "All Genres" else genre
            await self.apply_filters()
        elif event.select.id == "sort-select":
            self.current_sort = event.value
            await self.apply_filters()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle draft selection."""
        if event.item and self.filtered_drafts:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.filtered_drafts):
                draft_path, _ = self.filtered_drafts[idx]
                await self.open_draft(draft_path)

    async def load_drafts(self) -> None:
        """Load drafts list."""
        from bpui.utils.metadata.metadata import search_metadata
        from bpui.utils.migrate_logging import migrate_draft_metadata
        from pathlib import Path

        status = self.query_one("#status", Static)
        filter_info = self.query_one("#filter-info", Static)

        status.update("Loading drafts...")

        try:
            # Migrate drafts without metadata
            drafts_dir = Path.cwd() / "drafts"
            total, migrated = migrate_draft_metadata(drafts_dir)
            if migrated > 0:
                status.update(f"Migrated {migrated} drafts to use metadata")

            # Load all drafts with metadata
            self.all_drafts = search_metadata(drafts_dir)
            
            await self.apply_filters()

        except Exception as e:
            status.update(f"Error loading drafts: {e}")
            filter_info.update("")

    async def apply_filters(self) -> None:
        """Apply current filters and update the list."""
        from bpui.utils.metadata.metadata import search_metadata
        from pathlib import Path
        
        drafts_list = self.query_one("#drafts-list", ListView)
        status = self.query_one("#status", Static)
        filter_info = self.query_one("#filter-info", Static)
        
        try:
            drafts_dir = Path.cwd() / "drafts"
            
            # Apply search and filters
            self.filtered_drafts = search_metadata(
                drafts_dir,
                query=self.current_search,
                genre=self.current_genre,
                favorite_only=self.favorite_filter
            )
            
            # Sort results
            if self.current_sort == "newest":
                self.filtered_drafts.sort(key=lambda x: x[1].modified, reverse=True)
            elif self.current_sort == "oldest":
                self.filtered_drafts.sort(key=lambda x: x[1].modified)
            elif self.current_sort == "name_asc":
                self.filtered_drafts.sort(key=lambda x: x[1].character_name or x[0].name)
            elif self.current_sort == "name_desc":
                self.filtered_drafts.sort(key=lambda x: x[1].character_name or x[0].name, reverse=True)
            
            # Update list
            await drafts_list.clear()

            if not self.filtered_drafts:
                await drafts_list.append(ListItem(Static("[No drafts match filters]")))
                filter_text = "No matches"
            else:
                for draft_path, metadata in self.filtered_drafts:
                    # Format display name
                    char_name = metadata.character_name or draft_path.name
                    tags_str = f" [{', '.join(metadata.tags)}]" if metadata.tags else ""
                    fav_mark = "⭐ " if metadata.favorite else ""
                    genre_str = f" ({metadata.genre})" if metadata.genre else ""
                    
                    display = f"{fav_mark}{char_name}{genre_str}{tags_str}"
                    item = ListItem(Static(display))
                    if metadata.favorite:
                        item.add_class("favorite-item")
                    await drafts_list.append(item)
                
                filter_text = f"{len(self.filtered_drafts)} of {len(self.all_drafts)} drafts"
            
            # Update filter info
            active_filters = []
            if self.current_search:
                active_filters.append(f"search: '{self.current_search}'")
            if self.current_genre:
                active_filters.append(f"genre: {self.current_genre}")
            if self.favorite_filter:
                active_filters.append("favorites only")
            
            if active_filters:
                filter_info.update(f"{filter_text} | Filters: {', '.join(active_filters)}")
            else:
                filter_info.update(filter_text)
            
            status.update("Ready")

        except Exception as e:
            status.update(f"Error filtering drafts: {e}")


    async def open_draft(self, draft_dir) -> None:
        """Open a draft in review screen."""
        from bpui.utils.file_io.pack_io import load_draft
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
    
    def action_focus_search(self) -> None:
        """Focus the search input (F key)."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
    
    def action_toggle_favorite_filter(self) -> None:
        """Toggle favorites filter (R key)."""
        self.favorite_filter = not self.favorite_filter
        
        # Update button appearance
        button = self.query_one("#favorites-toggle", Button)
        if self.favorite_filter:
            button.label = "⭐ Show All [R]"
            button.variant = "warning"
        else:
            button.label = "⭐ Favorites Only [R]"
            button.variant = "default"
        
        # Reapply filters
        self.run_worker(self.apply_filters)
    
    def action_open_draft(self) -> None:
        """Open selected draft (Enter key)."""
        drafts_list = self.query_one("#drafts-list", ListView)
        if drafts_list.index is not None and self.filtered_drafts:
            idx = drafts_list.index
            if 0 <= idx < len(self.filtered_drafts):
                draft_path, _ = self.filtered_drafts[idx]
                self.run_worker(lambda: self.open_draft(draft_path))
    
    def action_delete_draft(self) -> None:
        """Delete selected draft (D key)."""
        drafts_list = self.query_one("#drafts-list", ListView)
        
        if drafts_list.index is None or not self.filtered_drafts:
            return
        
        idx = drafts_list.index
        if not 0 <= idx < len(self.filtered_drafts):
            return
        
        draft_path, _ = self.filtered_drafts[idx]
        
        # Show confirmation dialog
        self.app.push_screen(DeleteConfirmScreen(draft_path.name, self._confirm_delete))
    
    def _confirm_delete(self, confirmed: bool) -> None:
        """Handle delete confirmation."""
        if not confirmed:
            return
        
        drafts_list = self.query_one("#drafts-list", ListView)
        status = self.query_one("#status", Static)
        
        if drafts_list.index is None or not self.filtered_drafts:
            return
        
        idx = drafts_list.index
        if not 0 <= idx < len(self.filtered_drafts):
            return
        
        draft_path, _ = self.filtered_drafts[idx]
        
        try:
            from bpui.utils.file_io.pack_io import delete_draft
            delete_draft(draft_path)
            status.update(f"✓ Deleted: {draft_path.name}")
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
