"""Review and save screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static, TabbedContent, TabPane, TextArea, RichLog, Footer
from pathlib import Path


class ReviewScreen(Screen):
    """Review generated assets screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("e", "toggle_edit", "Edit Mode"),
        ("ctrl+s", "save_changes", "Save"),
        ("tab", "next_tab", "Next Tab"),
    ]

    CSS = """
    ReviewScreen {
        layout: vertical;
    }

    #review-container {
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

    #tabs {
        height: 1fr;
        margin-bottom: 1;
    }

    TextArea {
        height: 1fr;
        width: 100%;
    }

    .button-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .button-row Button {
        width: 1fr;
        margin-right: 1;
    }

    #validation-log {
        height: 10;
        border: solid $primary;
        margin-bottom: 1;
    }

    .status {
        text-align: center;
        color: $text-muted;
    }

    .error {
        color: $error;
    }

    .success {
        color: $success;
    }

    .dirty {
        color: $warning;
    }
    """

    def __init__(self, config, draft_dir: Path, assets: dict):
        """Initialize review screen."""
        super().__init__()
        self.config = config
        self.draft_dir = draft_dir
        self.assets = assets
        self.edit_mode = False
        self.dirty_assets = set()  # Track which assets have unsaved changes

    def compose(self) -> ComposeResult:
        """Compose review screen."""
        with Container(id="review-container"):
            yield Static(f"📝 Review: {self.draft_dir.name}", classes="title")

            with TabbedContent(id="tabs"):
                with TabPane("System Prompt"):
                    yield TextArea(
                        id="system_prompt_area",
                    )
                with TabPane("Post History"):
                    yield TextArea(
                        id="post_history_area",
                    )
                with TabPane("Character Sheet"):
                    yield TextArea(
                        id="character_sheet_area",
                    )
                with TabPane("Intro Scene"):
                    yield TextArea(
                        id="intro_scene_area",
                    )
                with TabPane("Intro Page"):
                    yield TextArea(
                        id="intro_page_area",
                    )
                with TabPane("A1111"):
                    yield TextArea(
                        id="a1111_area",
                    )
                with TabPane("Suno"):
                    yield TextArea(
                        id="suno_area",
                    )

            with Vertical(classes="button-row"):
                yield Button("✏️  [E] Edit Mode", id="toggle_edit", variant="default")
                yield Button("💾 [Ctrl+S] Save Changes", id="save", variant="success", disabled=True)
                yield Button("✓ Validate", id="validate", variant="primary")
                yield Button("📦 Export", id="export", variant="success")
                yield Button("⬅️  [Q] Back to Home", id="home")

            yield RichLog(id="validation-log", highlight=True, markup=True)
            yield Static("", id="status", classes="status")
            yield Footer()

    async def on_mount(self) -> None:
        """Handle mount - load text and auto-validate."""
        # Delay loading to ensure TextAreas are fully composed
        self.set_timer(0.1, self._delayed_load)
        
    def _delayed_load(self) -> None:
        """Load text after a short delay to ensure widgets exist."""
        self.run_worker(self._load_text, exclusive=True, name="load_text")
        
    async def on_worker_state_changed(self, event) -> None:
        """Handle worker state changes."""
        if event.worker.name == "load_text" and event.state == "SUCCESS":
            self.run_worker(self.validate_pack, exclusive=True)
    
    async def _load_text(self) -> None:
        """Load text into TextAreas after refresh."""
        try:
            areas = [
                ("system_prompt_area", "system_prompt"),
                ("post_history_area", "post_history"),
                ("character_sheet_area", "character_sheet"),
                ("intro_scene_area", "intro_scene"),
                ("intro_page_area", "intro_page"),
                ("a1111_area", "a1111"),
                ("suno_area", "suno"),
            ]
            
            for area_id, asset_name in areas:
                content = self.assets.get(asset_name, "")
                
                if content:
                    try:
                        area = self.query_one(f"#{area_id}", TextArea)
                        area.text = content
                        area.refresh()
                    except Exception:
                        pass
            
            # Set all TextAreas to read-only initially (edit mode starts disabled)
            for area_id, _ in areas:
                try:
                    area = self.query_one(f"#{area_id}", TextArea)
                    area.read_only = True
                except Exception:
                    pass
            
        except Exception:
            pass
    
    async def _load_text_areas(self) -> None:
        """Deprecated - kept for compatibility."""
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "home":
            # Check for unsaved changes
            if self.dirty_assets:
                status = self.query_one("#status", Static)
                status.update("⚠️  You have unsaved changes! Save or discard before leaving.")
                status.add_class("dirty")
                return
            
            from .home import HomeScreen
            self.app.switch_screen(HomeScreen(self.config))

        elif event.button.id == "toggle_edit":
            await self.toggle_edit_mode()

        elif event.button.id == "save":
            await self.save_changes()

        elif event.button.id == "validate":
            await self.validate_pack()

        elif event.button.id == "export":
            await self.export_pack()

    async def validate_pack(self) -> None:
        """Validate the pack."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)

        status.update("⏳ Validating pack...")
        status.remove_class("error")
        validation_log.clear()

        try:
            from ..validate import validate_pack

            result = validate_pack(self.draft_dir)

            validation_log.write("[bold cyan]Validation Results:[/]\n")
            validation_log.write(result["output"])

            if result["errors"]:
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result["success"]:
                status.update("✓ Validation passed")
            else:
                status.update("✗ Validation failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")

    async def export_pack(self) -> None:
        """Export the pack."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)

        status.update("⏳ Exporting pack...")
        status.remove_class("error")

        try:
            from ..export import export_character
            from ..parse_blocks import extract_character_name

            character_name = extract_character_name(self.assets["character_sheet"])
            if not character_name:
                character_name = "unnamed_character"

            model_name = self.config.model.split("/")[-1] if "/" in self.config.model else self.config.model

            result = export_character(character_name, self.draft_dir, model_name)

            validation_log.write("\n[bold cyan]Export Results:[/]\n")
            validation_log.write(result["output"])

            if result["errors"]:
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result["success"]:
                status.update(f"✓ Exported to {result['output_dir']}")
            else:
                status.update("✗ Export failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"\n[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")

    async def toggle_edit_mode(self) -> None:
        """Toggle between read-only and edit mode."""
        self.edit_mode = not self.edit_mode
        
        toggle_button = self.query_one("#toggle_edit", Button)
        save_button = self.query_one("#save", Button)
        status = self.query_one("#status", Static)
        
        # Update all TextArea widgets
        text_areas = [
            "#system_prompt_area",
            "#post_history_area",
            "#character_sheet_area",
            "#intro_scene_area",
            "#intro_page_area",
            "#a1111_area",
            "#suno_area",
        ]
        
        for area_id in text_areas:
            area = self.query_one(area_id, TextArea)
            area.read_only = not self.edit_mode
        
        if self.edit_mode:
            toggle_button.label = "👁️  View Mode"
            toggle_button.variant = "warning"
            save_button.disabled = len(self.dirty_assets) == 0
            status.update("✏️  Edit mode enabled - modify assets as needed")
            status.add_class("dirty")
        else:
            toggle_button.label = "✏️  Edit Mode"
            toggle_button.variant = "default"
            
            if self.dirty_assets:
                status.update("⚠️  Switched to view mode - you have unsaved changes")
                status.add_class("dirty")
            else:
                status.update("👁️  View mode enabled")
                status.remove_class("dirty")
    
    async def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes."""
        if not self.edit_mode:
            return
        
        # Map area IDs to asset names
        area_map = {
            "system_prompt_area": "system_prompt",
            "post_history_area": "post_history",
            "character_sheet_area": "character_sheet",
            "intro_scene_area": "intro_scene",
            "intro_page_area": "intro_page",
            "a1111_area": "a1111",
            "suno_area": "suno",
        }
        
        # Check if this area has changed
        asset_name = area_map.get(event.text_area.id)
        if asset_name and event.text_area.text != self.assets.get(asset_name, ""):
            self.dirty_assets.add(asset_name)
            
            # Enable save button
            save_button = self.query_one("#save", Button)
            save_button.disabled = False
            
            # Update status
            status = self.query_one("#status", Static)
            status.update(f"💾 Unsaved changes in: {', '.join(sorted(self.dirty_assets))}")
            status.add_class("dirty")
    
    async def save_changes(self) -> None:
        """Save edited assets back to files."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)
        
        if not self.dirty_assets:
            status.update("✓ No changes to save")
            return
        
        status.update("⏳ Saving changes...")
        status.remove_class("dirty")
        validation_log.clear()
        
        try:
            from ..parse_blocks import ASSET_FILENAMES
            
            # Map area IDs to asset names
            area_map = {
                "system_prompt_area": "system_prompt",
                "post_history_area": "post_history",
                "character_sheet_area": "character_sheet",
                "intro_scene_area": "intro_scene",
                "intro_page_area": "intro_page",
                "a1111_area": "a1111",
                "suno_area": "suno",
            }
            
            saved_count = 0
            for area_id, asset_name in area_map.items():
                if asset_name in self.dirty_assets:
                    area = self.query_one(f"#{area_id}", TextArea)
                    new_content = area.text
                    
                    # Update in-memory assets
                    self.assets[asset_name] = new_content
                    
                    # Write to file
                    filename = ASSET_FILENAMES.get(asset_name)
                    if filename:
                        file_path = self.draft_dir / filename
                        file_path.write_text(new_content)
                        saved_count += 1
                        validation_log.write(f"[green]✓ Saved {filename}[/]")
            
            # Clear dirty tracking
            self.dirty_assets.clear()
            
            # Disable save button
            save_button = self.query_one("#save", Button)
            save_button.disabled = True
            
            status.update(f"✓ Saved {saved_count} asset(s)")
            status.add_class("success")
            
            # Auto-validate after save
            validation_log.write("\n[dim]Running validation...[/dim]")
            await self.validate_pack()
            
        except Exception as e:
            validation_log.write(f"[bold red]✗ Error saving: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        from .home import HomeScreen
        self.app.switch_screen(HomeScreen(self.config))
    
    def action_toggle_edit(self) -> None:
        """Toggle edit mode (E key)."""
        self.run_worker(self.toggle_edit_mode, exclusive=False)
    
    def action_save_changes(self) -> None:
        """Save changes (Ctrl+S)."""
        save_button = self.query_one("#save", Button)
        if not save_button.disabled:
            self.run_worker(self.save_changes, exclusive=False)
    
    def action_next_tab(self) -> None:
        """Switch to next tab (Tab key)."""
        tabs = self.query_one("#tabs", TabbedContent)
        # Get all tab IDs
        tab_ids = [pane.id for pane in tabs.query(TabPane)]
        if not tab_ids:
            return
        
        # Find current tab index
        try:
            current_idx = tab_ids.index(tabs.active)
            next_idx = (current_idx + 1) % len(tab_ids)
            tabs.active = tab_ids[next_idx]
        except (ValueError, IndexError):
            # Default to first tab if something goes wrong
            tabs.active = tab_ids[0]
