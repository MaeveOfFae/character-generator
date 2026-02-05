"""Review and save screen for Blueprint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, TabbedContent, TabPane, TextArea, RichLog, Footer, Input

if TYPE_CHECKING:
    from .review import ReviewScreen


class ReviewScreen(Screen):
    """Review generated assets screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("e", "toggle_edit", "Edit Mode"),
        ("ctrl+s", "save_changes", "Save"),
        ("tab", "next_tab", "Next Tab"),
        ("c", "toggle_chat", "Chat"),
        ("o", "save_to_file", "Save to File"),
        ("ctrl+r", "regenerate_asset", "Regenerate"),
        ("t", "edit_tags", "Edit Tags"),
        ("f", "toggle_favorite", "Toggle Favorite"),
        ("g", "edit_genre", "Edit Genre"),
        ("n", "edit_notes", "Edit Notes"),
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

    #metadata-section {
        layout: horizontal;
        height: auto;
        padding: 1;
        border: solid $accent;
        margin-bottom: 1;
    }

    #metadata-info {
        width: 2fr;
    }

    #metadata-buttons {
        width: 1fr;
        layout: horizontal;
    }

    #metadata-buttons Button {
        margin-left: 1;
    }

    .favorite-star {
        color: $warning;
    }

    #main-split {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #left-panel {
        width: 100%;
        layout: vertical;
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

    #chat-panel {
        width: 30%;
        border-left: solid $primary;
        padding: 1;
    }

    #chat-panel.hidden {
        display: none;
    }

    #chat-log {
        height: 1fr;
        border: solid $accent;
        margin-bottom: 1;
    }

    #chat-input {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self, config, draft_dir: Path, assets: dict, seed: str = None, mode: str = None, model: str = None):
        """Initialize review screen."""
        super().__init__()
        self.config = config
        self.draft_dir = draft_dir
        self.assets = assets
        self.edit_mode = False
        self.dirty_assets = set()  # Track which assets have unsaved changes
        self.chat_visible = False
        self.chat_messages: list[dict] = []  # Chat history
        self.chat_generating = False
        
        # Load metadata or use provided values
        from ..metadata import DraftMetadata
        metadata = DraftMetadata.load(draft_dir)
        
        if metadata:
            self.seed = metadata.seed
            self.mode = metadata.mode
            self.model = metadata.model
        else:
            # Use provided values or defaults
            self.seed = seed or "unknown"
            self.mode = mode
            self.model = model or config.model

    def compose(self) -> ComposeResult:
        """Compose review screen."""
        with Container(id="review-container"):
            yield Static(f"📝 Review: {self.draft_dir.name}", classes="title")
            
            # Metadata section
            with Horizontal(id="metadata-section"):
                yield Static("", id="metadata-info")
                with Horizontal(id="metadata-buttons"):
                    yield Button("⭐ [F] Favorite", id="favorite-toggle", variant="default")
                    yield Button("🏷️  [T] Tags", id="edit-tags", variant="default")
                    yield Button("🎭 [G] Genre", id="edit-genre", variant="default")
                    yield Button("📝 [N] Notes", id="edit-notes", variant="default")

            with Horizontal(id="main-split"):
                with Vertical(id="left-panel"):
                    with TabbedContent(id="tabs"):
                        with TabPane("System Prompt", id="system-prompt-tab"):
                            yield TextArea(
                                self.assets.get("system_prompt", ""),
                                id="system_prompt_area",
                                read_only=True,
                            )
                        with TabPane("Post History", id="post-history-tab"):
                            yield TextArea(
                                self.assets.get("post_history", ""),
                                id="post_history_area",
                                read_only=True,
                            )
                        with TabPane("Character Sheet", id="character-sheet-tab"):
                            yield TextArea(
                                self.assets.get("character_sheet", ""),
                                id="character_sheet_area",
                                read_only=True,
                            )
                        with TabPane("Intro Scene", id="intro-scene-tab"):
                            yield TextArea(
                                self.assets.get("intro_scene", ""),
                                id="intro_scene_area",
                                read_only=True,
                            )
                        with TabPane("Intro Page", id="intro-page-tab"):
                            yield TextArea(
                                self.assets.get("intro_page", ""),
                                id="intro_page_area",
                                read_only=True,
                            )
                        with TabPane("A1111", id="a1111-tab"):
                            yield TextArea(
                                self.assets.get("a1111", ""),
                                id="a1111_area",
                                read_only=True,
                            )
                        with TabPane("Suno", id="suno-tab"):
                            yield TextArea(
                                self.assets.get("suno", ""),
                                id="suno_area",
                                read_only=True,
                            )

                    with Vertical(classes="button-row"):
                        yield Button("✏️  [E] Edit Mode", id="toggle_edit", variant="default")
                        yield Button("💾 [Ctrl+S] Save Changes", id="save", variant="success", disabled=True)
                        yield Button("🔄 [Ctrl+R] Regenerate Asset", id="regenerate", variant="primary")
                        yield Button("✓ Validate", id="validate", variant="primary")
                        yield Button("📦 Export", id="export", variant="success")
                        yield Button("💬 [C] Chat", id="chat_toggle", variant="default")
                        yield Button("📁 [O] Save to File", id="save_file", variant="default")
                        yield Button("⬅️  [Q] Back to Home", id="home")

                    yield RichLog(id="validation-log", highlight=True, markup=True)
                    yield Static("", id="status", classes="status")

                # Chat panel (initially hidden)
                with Vertical(id="chat-panel", classes="hidden"):
                    yield Static("💬 Asset Chat", classes="title")
                    yield RichLog(id="chat-log", highlight=True, markup=True)
                    yield Input(
                        placeholder="Ask about or request changes to the current asset...",
                        id="chat-input",
                    )
                    yield Button("Send", id="chat-send", variant="primary")
            
        yield Footer()

    async def on_mount(self) -> None:
        """Handle mount - load text and auto-validate."""
        # Update metadata display
        self.update_metadata_display()
        # Run validation after a brief delay
        self.set_timer(0.3, lambda: self.run_worker(self.validate_pack, exclusive=True))
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in chat input."""
        if event.input.id == "chat-input":
            await self.send_chat_message()
    
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

        elif event.button.id == "regenerate":
            await self.regenerate_current_asset()

        elif event.button.id == "validate":
            await self.validate_pack()

        elif event.button.id == "export":
            await self.export_pack()

        elif event.button.id == "chat_toggle":
            self.toggle_chat()

        elif event.button.id == "chat-send":
            await self.send_chat_message()

        elif event.button.id == "save_file":
            self.show_save_dialog()

        elif event.button.id == "favorite-toggle":
            await self.toggle_favorite()

        elif event.button.id == "edit-tags":
            self.show_tags_dialog()

        elif event.button.id == "edit-genre":
            self.show_genre_dialog()

        elif event.button.id == "edit-notes":
            self.show_notes_dialog()

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
            validation_log.write(result.get("output", "No validation output"))

            if result.get("errors"):
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result.get("success"):
                status.update("✓ Validation passed")
            else:
                status.update("✗ Validation failed")
                status.add_class("error")

        except Exception as e:
            validation_log.write(f"[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")

    async def export_pack(self) -> None:
        """Export the pack - show preset selector dialog."""
        self.app.push_screen(ExportPresetDialog(self, self.draft_dir, self.assets, self.config))
    
    async def do_export(self, preset_name: Optional[str] = None) -> None:
        """Perform the actual export with optional preset."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)

        if preset_name:
            status.update(f"⏳ Exporting with {preset_name} preset...")
        else:
            status.update("⏳ Exporting pack...")
        status.remove_class("error")

        try:
            from ..export import export_character
            from ..parse_blocks import extract_character_name

            character_sheet = self.assets.get("character_sheet", "")
            character_name = extract_character_name(character_sheet)
            if not character_name:
                character_name = "unnamed_character"

            model_name = self.config.model.split("/")[-1] if "/" in self.config.model else self.config.model

            result = export_character(
                character_name=character_name,
                source_dir=self.draft_dir,
                model=model_name,
                preset_name=preset_name
            )

            validation_log.write("\n[bold cyan]Export Results:[/]\n")
            validation_log.write(result.get("output", "No export output"))

            if result.get("errors"):
                validation_log.write(f"\n[bold red]Errors:[/]\n{result['errors']}")

            if result.get("success"):
                output_dir = result.get("output_dir", "unknown location")
                status.update(f"✓ Exported to {output_dir}")
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
        asset_name = area_map.get(event.text_area.id or "")
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
                    filename = ASSET_FILENAMES.get(asset_name, "")
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
    
    async def regenerate_current_asset(self) -> None:
        """Regenerate the currently visible asset using the original seed."""
        status = self.query_one("#status", Static)
        validation_log = self.query_one("#validation-log", RichLog)
        
        # Check if seed is available
        if not self.seed or self.seed == "unknown":
            validation_log.write("[bold red]✗ Cannot regenerate: No seed available[/]")
            validation_log.write("[dim]This draft doesn't have the original seed saved.[/dim]")
            validation_log.write("[dim]Seed tracking was added in a recent update.[/dim]")
            status.update("✗ No seed available for regeneration")
            status.add_class("error")
            return
        
        # Get active tab and map to asset
        tabs = self.query_one("#tabs", TabbedContent)
        active_tab = str(tabs.active)
        
        tab_to_asset = {
            "system-prompt": "system_prompt",
            "post-history": "post_history",
            "character-sheet": "character_sheet",
            "intro-scene": "intro_scene",
            "intro-page": "intro_page",
            "a1111": "a1111",
            "suno": "suno",
        }
        
        asset_name = tab_to_asset.get(active_tab)
        if not asset_name:
            validation_log.write(f"[bold red]✗ Unknown tab: {active_tab}[/]")
            return
        
        validation_log.clear()
        validation_log.write(f"[bold cyan]Regenerating: {asset_name}[/]")
        validation_log.write(f"[dim]Seed: {self.seed}[/dim]")
        validation_log.write(f"[dim]Mode: {self.mode or 'Auto'}[/dim]\n")
        status.update(f"⏳ Regenerating {asset_name}...")
        status.remove_class("error")
        status.remove_class("success")
        
        try:
            # Build prior assets dict (only higher-tier assets for hierarchy)
            from ..parse_blocks import ASSET_ORDER
            asset_index = ASSET_ORDER.index(asset_name)
            prior_assets = {}
            for i in range(asset_index):
                prior_name = ASSET_ORDER[i]
                if prior_name in self.assets:
                    prior_assets[prior_name] = self.assets[prior_name]
            
            # Build prompt for this specific asset
            from ..prompting import build_asset_prompt
            system_prompt, user_prompt = build_asset_prompt(
                asset_name=asset_name,
                seed=self.seed,
                mode=self.mode,
                prior_assets=prior_assets if prior_assets else None
            )
            
            validation_log.write("[dim]Creating LLM engine...[/dim]")
            
            # Create LLM engine
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            
            engine_config = {
                "model": self.model or self.config.model,
                "api_key": self.config.api_key,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            
            if self.config.engine == "litellm":
                engine = LiteLLMEngine(**engine_config)
            else:
                engine_config["base_url"] = self.config.base_url
                engine = OpenAICompatEngine(**engine_config)
            
            validation_log.write("[dim]Streaming generation...[/dim]\n")
            
            # Stream generation
            raw_output = ""
            chunk_count = 0
            stream = engine.generate_stream(system_prompt, user_prompt)
            
            async for chunk in stream:
                raw_output += chunk
                chunk_count += 1
                
                # Show progress every 10 chunks
                if chunk_count % 10 == 0:
                    validation_log.write(".", end="")
            
            validation_log.write(f"\n\n[dim]Received {len(raw_output)} characters[/dim]")
            
            # Extract codeblock from output
            import re
            pattern = r"```(?:[a-z]*\n)?(.*?)```"
            matches = re.findall(pattern, raw_output, re.DOTALL)
            
            if not matches:
                # No codeblock found, use raw output
                new_content = raw_output.strip()
            else:
                # Use first codeblock
                new_content = matches[0].strip()
            
            validation_log.write(f"[green]✓ Generated {len(new_content)} characters[/]")
            
            # Update TextArea
            area_mapping = {
                "system_prompt": "system_prompt_area",
                "post_history": "post_history_area",
                "character_sheet": "character_sheet_area",
                "intro_scene": "intro_scene_area",
                "intro_page": "intro_page_area",
                "a1111": "a1111_area",
                "suno": "suno_area",
            }
            
            area_id = area_mapping.get(asset_name)
            if area_id:
                area = self.query_one(f"#{area_id}", TextArea)
                area.text = new_content
                
                # Mark as dirty and enable save
                self.dirty_assets.add(asset_name)
                save_button = self.query_one("#save", Button)
                save_button.disabled = False
                
                # Update in-memory assets
                self.assets[asset_name] = new_content
                
                validation_log.write(f"[green]✓ Updated {asset_name} (unsaved)[/]")
                status.update(f"✓ Regenerated {asset_name} - Save to keep changes")
                status.add_class("success")
            
        except Exception as e:
            validation_log.write(f"\n[bold red]✗ Error during regeneration: {e}[/]")
            status.update(f"✗ Regeneration failed: {e}")
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
            tabs.active = "system-prompt"
            return
        
        # Find current tab index
        try:
            current_active = tabs.active
            if current_active is None or current_active not in tab_ids:
                current_active = cast(str, tab_ids[0])
            current_idx = tab_ids.index(current_active)
            next_idx = (current_idx + 1) % len(tab_ids)
            tabs.active = cast(str, tab_ids[next_idx])
        except (ValueError, IndexError):
            # Default to first tab if something goes wrong
            tabs.active = cast(str, tab_ids[0])
    
    def action_toggle_chat(self) -> None:
        """Toggle chat panel (C key)."""
        self.toggle_chat()
    
    def action_regenerate_asset(self) -> None:
        """Regenerate current asset (Ctrl+R)."""
        self.run_worker(self.regenerate_current_asset, exclusive=False)
    
    def toggle_chat(self) -> None:
        """Show or hide chat panel."""
        self.chat_visible = not self.chat_visible
        chat_panel = self.query_one("#chat-panel")
        
        if self.chat_visible:
            chat_panel.remove_class("hidden")
            left_panel = self.query_one("#left-panel")
            left_panel.styles.width = "70%"
        else:
            chat_panel.add_class("hidden")
            left_panel = self.query_one("#left-panel")
            left_panel.styles.width = "100%"
    
    async def send_chat_message(self) -> None:
        """Send user message to chat and get LLM response."""
        if self.chat_generating:
            return
        
        chat_input = self.query_one("#chat-input", Input)
        chat_log = self.query_one("#chat-log", RichLog)
        
        user_message = chat_input.value.strip()
        if not user_message:
            return
        
        # Clear input
        chat_input.value = ""
        
        # Display user message
        chat_log.write(f"[bold cyan]You:[/] {user_message}")
        
        # Add to history
        self.chat_messages.append({"role": "user", "content": user_message})
        
        # Mark as generating
        self.chat_generating = True
        chat_log.write("[dim]Assistant is typing...[/dim]")
        
        try:
            # Build system prompt with asset context
            system_prompt = await self.build_chat_system_prompt()
            
            # Build full messages list
            messages = [{"role": "system", "content": system_prompt}] + self.chat_messages
            
            # Get LLM engine
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            
            if self.config.engine == "litellm":
                engine = LiteLLMEngine(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            else:
                engine = OpenAICompatEngine(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            
            # Stream response
            assistant_response = ""
            chat_log.write("[bold green]Assistant:[/] ")
            
            stream = engine.generate_chat_stream(messages)
            async for chunk in stream:
                assistant_response += chunk
                chat_log.write(chunk)
                chat_log.refresh()
            
            chat_log.write("")  # Newline
            
            # Add assistant response to history
            self.chat_messages.append({"role": "assistant", "content": assistant_response})
            
            # Check if response contains edited asset
            await self.parse_edit_from_response(assistant_response)
            
        except Exception as e:
            chat_log.write(f"[bold red]Error:[/] {e}")
        finally:
            self.chat_generating = False
    
    async def build_chat_system_prompt(self) -> str:
        """Build system prompt for chat with asset context."""
        # Get active tab name
        tabs = self.query_one("#tabs", TabbedContent)
        active_tab = str(tabs.active)
        
        # Map tab IDs to asset names
        tab_to_asset = {
            "system-prompt": "system_prompt",
            "post-history": "post_history",
            "character-sheet": "character_sheet",
            "intro-scene": "intro_scene",
            "intro-page": "intro_page",
            "a1111": "a1111",
            "suno": "suno",
        }
        
        asset_name = tab_to_asset.get(active_tab, "system_prompt")
        
        # Get current asset content
        asset_areas = {
            "system_prompt": "system_prompt_area",
            "post_history": "post_history_area",
            "character_sheet": "character_sheet_area",
            "intro_scene": "intro_scene_area",
            "intro_page": "intro_page_area",
            "a1111": "a1111_area",
            "suno": "suno_area",
        }
        
        area_id = asset_areas.get(asset_name, "system_prompt_area")
        area = self.query_one(f"#{area_id}", TextArea)
        current_content = area.text
        
        # Get character sheet for context
        sheet_area = self.query_one("#character_sheet_area", TextArea)
        character_sheet = sheet_area.text
        
        # Build prompt
        from ..prompting import build_refinement_chat_system
        
        return build_refinement_chat_system(
            asset_name=asset_name,
            current_content=current_content,
            character_sheet=character_sheet,
        )
    
    async def parse_edit_from_response(self, response: str) -> None:
        """Check if response contains edited asset and apply it."""
        # Look for codeblock in response
        if "```" not in response:
            return
        
        # Extract codeblock content
        lines = response.split("\n")
        in_block = False
        block_lines = []
        
        for line in lines:
            if line.startswith("```"):
                if in_block:
                    # End of block
                    break
                else:
                    # Start of block
                    in_block = True
                    continue
            
            if in_block:
                block_lines.append(line)
        
        if not block_lines:
            return
        
        edited_content = "\n".join(block_lines)
        
        # Apply to current asset
        await self.apply_edit_to_asset(edited_content)
    
    async def apply_edit_to_asset(self, new_content: str) -> None:
        """Apply edited content to current asset TextArea."""
        # Get active tab
        tabs = self.query_one("#tabs", TabbedContent)
        active_tab = str(tabs.active)
        
        # Map tab IDs to area IDs
        tab_to_area = {
            "system-prompt": "system_prompt_area",
            "post-history": "post_history_area",
            "character-sheet": "character_sheet_area",
            "intro-scene": "intro_scene_area",
            "intro-page": "intro_page_area",
            "a1111": "a1111_area",
            "suno": "suno_area",
        }
        
        tab_to_asset = {
            "system-prompt": "system_prompt",
            "post-history": "post_history",
            "character-sheet": "character_sheet",
            "intro-scene": "intro_scene",
            "intro-page": "intro_page",
            "a1111": "a1111",
            "suno": "suno",
        }
        
        area_id = tab_to_area.get(active_tab)
        asset_name = tab_to_asset.get(active_tab)
        
        if not area_id or not asset_name:
            return
        
        # Update TextArea
        area = self.query_one(f"#{area_id}", TextArea)
        area.text = new_content
        
        # Mark as dirty
        self.dirty_assets.add(asset_name)
        
        # Enable save button
        save_button = self.query_one("#save", Button)
        save_button.disabled = False
        
        # Update status
        status = self.query_one("#status", Static)
        status.update(f"✏️  Chat applied edits to {asset_name} (unsaved)")
        status.add_class("dirty")
        
        # Log to chat
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(f"[bold yellow]✓ Applied edits to {asset_name}[/bold yellow]")
    
    def show_save_dialog(self) -> None:
        """Show save to file dialog."""
        self.app.push_screen(SaveFileDialog(self))
    
    def action_save_to_file(self) -> None:
        """Show save to file dialog (O key)."""
        self.show_save_dialog()
    
    def update_metadata_display(self) -> None:
        """Update the metadata information display."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata.create_default(self.draft_dir)
        
        metadata_info = self.query_one("#metadata-info", Static)
        
        # Format display
        fav_mark = "⭐ " if metadata.favorite else ""
        tags_str = f"🏷️  {', '.join(metadata.tags)}" if metadata.tags else "No tags"
        genre_str = f"🎭 {metadata.genre}" if metadata.genre else "No genre"
        notes_str = f"📝 {metadata.notes[:50]}{'...' if len(metadata.notes) > 50 else ''}" if metadata.notes else "No notes"
        
        metadata_info.update(f"{fav_mark}{tags_str} | {genre_str} | {notes_str}")
        
        # Update favorite button
        fav_button = self.query_one("#favorite-toggle", Button)
        if metadata.favorite:
            fav_button.label = "⭐ [F] Favorited"
            fav_button.variant = "warning"
        else:
            fav_button.label = "☆ [F] Favorite"
            fav_button.variant = "default"
    
    async def toggle_favorite(self) -> None:
        """Toggle favorite status (F key)."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata.create_default(self.draft_dir)
        
        metadata.favorite = not metadata.favorite
        metadata.update_modified()
        metadata.save(self.draft_dir)
        
        self.update_metadata_display()
        
        status = self.query_one("#status", Static)
        if metadata.favorite:
            status.update("⭐ Added to favorites")
        else:
            status.update("Removed from favorites")
    
    def action_toggle_favorite(self) -> None:
        """Action to toggle favorite (F key)."""
        self.run_worker(self.toggle_favorite)
    
    def show_tags_dialog(self) -> None:
        """Show tags editor dialog."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata.create_default(self.draft_dir)
        
        self.app.push_screen(TagsEditorDialog(self.draft_dir, metadata.tags, self.update_metadata_display))
    
    def action_edit_tags(self) -> None:
        """Action to edit tags (T key)."""
        self.show_tags_dialog()
    
    def show_genre_dialog(self) -> None:
        """Show genre editor dialog."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata.create_default(self.draft_dir)
        
        self.app.push_screen(GenreEditorDialog(self.draft_dir, metadata.genre or "", self.update_metadata_display))
    
    def action_edit_genre(self) -> None:
        """Action to edit genre (G key)."""
        self.show_genre_dialog()
    
    def show_notes_dialog(self) -> None:
        """Show notes editor dialog."""
        from ..metadata import DraftMetadata
        
        metadata = DraftMetadata.load(self.draft_dir)
        if not metadata:
            metadata = DraftMetadata.create_default(self.draft_dir)
        
        self.app.push_screen(NotesEditorDialog(self.draft_dir, metadata.notes or "", self.update_metadata_display))
    
    def action_edit_notes(self) -> None:
        """Action to edit notes (N key)."""
        self.show_notes_dialog()


class TagsEditorDialog(Screen):
    """Dialog for editing tags."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]
    
    CSS = """
    TagsEditorDialog {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 70;
        height: 20;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }
    
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    
    #input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #help {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    """
    
    def __init__(self, draft_dir: Path, tags: list[str], callback):
        super().__init__()
        self.draft_dir = draft_dir
        self.tags = tags
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("🏷️  Edit Tags", id="title")
            yield Static("Enter tags separated by commas", id="help")
            yield Input(value=", ".join(self.tags), id="input")
            with Horizontal(id="buttons"):
                yield Button("💾 [Ctrl+S] Save", id="save", variant="success")
                yield Button("[Q] Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()
    
    def action_save(self) -> None:
        from ..metadata import DraftMetadata
        
        input_widget = self.query_one("#input", Input)
        tags_str = input_widget.value
        
        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Save to metadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.tags = tags
            metadata.update_modified()
            metadata.save(self.draft_dir)
        
        self.app.pop_screen()
        if self.callback:
            self.callback()
    
    def action_cancel(self) -> None:
        self.app.pop_screen()


class GenreEditorDialog(Screen):
    """Dialog for editing genre."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]
    
    CSS = """
    GenreEditorDialog {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 60;
        height: 15;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }
    
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    
    #input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    """
    
    def __init__(self, draft_dir: Path, genre: str, callback):
        super().__init__()
        self.draft_dir = draft_dir
        self.genre = genre
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("🎭 Edit Genre", id="title")
            yield Input(value=self.genre, placeholder="e.g., Fantasy, Sci-Fi, Modern...", id="input")
            with Horizontal(id="buttons"):
                yield Button("💾 [Ctrl+S] Save", id="save", variant="success")
                yield Button("[Q] Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()
    
    def action_save(self) -> None:
        from ..metadata import DraftMetadata
        
        input_widget = self.query_one("#input", Input)
        genre = input_widget.value.strip()
        
        # Save to metadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.genre = genre
            metadata.update_modified()
            metadata.save(self.draft_dir)
        
        self.app.pop_screen()
        if self.callback:
            self.callback()
    
    def action_cancel(self) -> None:
        self.app.pop_screen()


class NotesEditorDialog(Screen):
    """Dialog for editing notes."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]
    
    CSS = """
    NotesEditorDialog {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 80;
        height: 25;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }
    
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    
    #textarea {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    """
    
    def __init__(self, draft_dir: Path, notes: str, callback):
        super().__init__()
        self.draft_dir = draft_dir
        self.notes = notes
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("📝 Edit Notes", id="title")
            yield TextArea(text=self.notes, id="textarea")
            with Horizontal(id="buttons"):
                yield Button("💾 [Ctrl+S] Save", id="save", variant="success")
                yield Button("[Q] Cancel", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()
    
    def action_save(self) -> None:
        from ..metadata import DraftMetadata
        
        textarea = self.query_one("#textarea", TextArea)
        notes = textarea.text.strip()
        
        # Save to metadata
        metadata = DraftMetadata.load(self.draft_dir)
        if metadata:
            metadata.notes = notes
            metadata.update_modified()
            metadata.save(self.draft_dir)
        
        self.app.pop_screen()
        if self.callback:
            self.callback()
    
    def action_cancel(self) -> None:
        self.app.pop_screen()


class SaveFileDialog(Screen):
    """Dialog for saving assets to custom file locations."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("enter", "confirm", "Save"),
    ]
    
    CSS = """
    SaveFileDialog {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 80;
        height: 25;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }
    
    #title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    #options {
        height: 12;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }
    
    #path-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
    }
    
    #path-label {
        width: 15;
        content-align: left middle;
    }
    
    #path-input {
        width: 1fr;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    
    .radio-option {
        height: 2;
    }
    """
    
    def __init__(self, parent_screen: ReviewScreen):
        """Initialize save dialog."""
        super().__init__()
        self.parent_screen = parent_screen
        self.selected_option = "current"  # current, all, custom
        self.custom_path = ""
    
    def compose(self) -> ComposeResult:
        """Compose save dialog."""
        with Vertical(id="dialog"):
            yield Static("📁 Save to File", id="title")
            
            with Vertical(id="options"):
                yield Static("Choose what to save:", classes="radio-option")
                yield Static("  [1] Current asset only", id="opt-current")
                yield Static("  [2] All assets (zip archive)", id="opt-all")
                yield Static("  [3] Custom selection", id="opt-custom")
                yield Static("")
            
            with Horizontal(id="path-row"):
                yield Static("Output path:", id="path-label")
                yield Input(placeholder=f"{self.parent_screen.draft_dir.parent}/", id="path-input")
            
            with Container(id="buttons"):
                yield Button("Save", id="confirm", variant="primary")
                yield Button("Cancel", id="cancel")
    
    def on_key(self, event) -> None:
        """Handle key presses for option selection."""
        if event.key == "1":
            self.selected_option = "current"
            self._update_option_display()
        elif event.key == "2":
            self.selected_option = "all"
            self._update_option_display()
        elif event.key == "3":
            self.selected_option = "custom"
            self._update_option_display()
    
    def _update_option_display(self) -> None:
        """Update display to show selected option."""
        opt_current = self.query_one("#opt-current", Static)
        opt_all = self.query_one("#opt-all", Static)
        opt_custom = self.query_one("#opt-custom", Static)
        
        # Reset all
        opt_current.update("  [1] Current asset only")
        opt_all.update("  [2] All assets (zip archive)")
        opt_custom.update("  [3] Custom selection")
        
        # Highlight selected
        if self.selected_option == "current":
            opt_current.update("  [1] [bold green]✓[/] Current asset only")
        elif self.selected_option == "all":
            opt_all.update("  [2] [bold green]✓[/] All assets (zip archive)")
        elif self.selected_option == "custom":
            opt_custom.update("  [3] [bold green]✓[/] Custom selection")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm":
            await self.confirm_save()
        else:
            self.app.pop_screen()
    
    def action_confirm(self) -> None:
        """Confirm save (Enter key)."""
        self.run_worker(self.confirm_save, exclusive=False)
    
    def action_cancel(self) -> None:
        """Cancel (Escape/Q keys)."""
        self.app.pop_screen()
    
    async def confirm_save(self) -> None:
        """Perform the save operation."""
        path_input = self.query_one("#path-input", Input)
        custom_path = path_input.value.strip()
        
        if not custom_path:
            custom_path = str(self.parent_screen.draft_dir.parent)
        
        output_path = Path(custom_path)
        
        try:
            if self.selected_option == "current":
                # Save current asset only
                await self._save_current_asset(output_path)
            elif self.selected_option == "all":
                # Save all assets as zip
                await self._save_all_assets(output_path)
            elif self.selected_option == "custom":
                # Custom selection - save all for now
                await self._save_all_assets(output_path)
            
            self.app.pop_screen()
            
        except Exception as e:
            # Show error
            path_input.value = f"Error: {e}"
    
    async def _save_current_asset(self, output_path: Path) -> None:
        """Save only the currently displayed asset."""
        # Get active tab
        tabs = self.parent_screen.query_one("#tabs", TabbedContent)
        active_tab = str(tabs.active)
        
        # Map tab IDs to asset names
        tab_to_asset = {
            "system-prompt": ("system_prompt", "system_prompt.txt"),
            "post-history": ("post_history", "post_history.txt"),
            "character-sheet": ("character_sheet", "character_sheet.txt"),
            "intro-scene": ("intro_scene", "intro_scene.txt"),
            "intro-page": ("intro_page", "intro_page.md"),
            "a1111": ("a1111", "a1111_prompt.txt"),
            "suno": ("suno", "suno_prompt.txt"),
        }
        
        asset_info = tab_to_asset.get(active_tab)
        if not asset_info:
            return
        
        asset_name, default_filename = asset_info
        content = self.parent_screen.assets.get(asset_name, "")
        
        if not content:
            return
        
        # Save to file
        if output_path.is_dir():
            output_file = output_path / default_filename
        else:
            output_file = output_path
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content)
        
        # Update parent status
        status = self.parent_screen.query_one("#status", Static)
        status.update(f"✓ Saved {asset_name} to {output_file}")
        status.add_class("success")
    
    async def _save_all_assets(self, output_path: Path) -> None:
        """Save all assets as a zip archive."""
        import zipfile
        import io
        from datetime import datetime
        
        # Determine output file path
        if output_path.is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_path / f"{self.parent_screen.draft_dir.name}_{timestamp}.zip"
        else:
            output_file = output_path
            if not output_file.suffix:
                output_file = output_file.with_suffix(".zip")
        
        # Create zip file
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            from ..parse_blocks import ASSET_FILENAMES
            
            for asset_name, content in self.parent_screen.assets.items():
                if isinstance(asset_name, str):
                    filename = ASSET_FILENAMES.get(asset_name)
                    if filename and content:
                        zf.writestr(filename, content)
        
        # Update parent status
        status = self.parent_screen.query_one("#status", Static)
        status.update(f"✓ Saved all assets to {output_file}")
        status.add_class("success")


class ExportPresetDialog(Screen):
    """Dialog for selecting export preset."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("enter", "confirm", "Export"),
    ]
    
    CSS = """
    ExportPresetDialog {
        layout: horizontal;
        align: center middle;
    }
    
    #dialog {
        width: 70;
        height: 30;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }
    
    #title {
        text-align: center;
        margin-bottom: 1;
    }
    
    #help {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #preset-list {
        height: 1fr;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    #buttons {
        layout: horizontal;
        height: 3;
    }
    
    #buttons Button {
        width: 1fr;
    }
    """
    
    def __init__(self, parent_screen, draft_dir: Path, assets: dict, config):
        super().__init__()
        self.parent_screen = parent_screen
        self.draft_dir = draft_dir
        self.assets = assets
        self.config = config
        self.presets = []
        self.selected_preset = None
    
    def compose(self) -> ComposeResult:
        from textual.widgets import ListView, ListItem
        
        with Vertical(id="dialog"):
            yield Static("📦 Export with Preset", id="title")
            yield Static("Select an export format or use default", id="help")
            yield ListView(id="preset-list")
            with Horizontal(id="buttons"):
                yield Button("📤 Export Default", id="export-default", variant="primary")
                yield Button("[Enter] Export Selected", id="export-preset", variant="success")
                yield Button("[Q] Cancel", id="cancel")
    
    async def on_mount(self) -> None:
        """Load available presets."""
        from ..export_presets import list_presets
        
        preset_list = self.query_one("#preset-list", ListView)
        
        # Load presets
        self.presets = list_presets()
        
        if not self.presets:
            await preset_list.append(ListItem(Static("[No presets found]")))
        else:
            for preset_name, preset_path in self.presets:
                await preset_list.append(ListItem(Static(f"📋 {preset_name} - {preset_path.stem}")))
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle preset selection."""
        if event.item and self.presets:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.presets):
                self.selected_preset = self.presets[idx][1].stem
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export-default":
            self.app.pop_screen()
            self.parent_screen.run_worker(lambda: self.parent_screen.do_export(preset_name=None))
        elif event.button.id == "export-preset":
            self.action_confirm()
        else:
            self.action_cancel()
    
    def action_confirm(self) -> None:
        """Export with selected preset."""
        if not self.selected_preset and self.presets:
            # Use first preset if none selected
            self.selected_preset = self.presets[0][1].stem
        
        self.app.pop_screen()
        if self.selected_preset:
            self.parent_screen.run_worker(lambda: self.parent_screen.do_export(preset_name=self.selected_preset))
        else:
            self.parent_screen.run_worker(lambda: self.parent_screen.do_export(preset_name=None))
    
    def action_cancel(self) -> None:
        self.app.pop_screen()
