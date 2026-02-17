"""Offspring generator screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, RichLog, Footer, Select, Input, ListView, ListItem


class OffspringScreen(Screen):
    """Offspring generation screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("ctrl+c", "cancel_generation", "Cancel"),
        ("enter", "start_offspring", "Generate"),
        ("1", "select_parent1", "Parent 1"),
        ("2", "select_parent2", "Parent 2"),
    ]

    def __init__(self, config):
        """Initialize offspring screen."""
        super().__init__()
        self.config = config
        self.parent1_path = None
        self.parent2_path = None
        self.parent1_assets = {}
        self.parent2_assets = {}
        self.parent1_name = ""
        self.parent2_name = ""
        self.is_generating = False
        self.templates = []

    def compose(self) -> ComposeResult:
        """Compose offspring screen."""
        with Container(id="offspring-container"):
            yield Static("👶 Offspring Generator", classes="title")

            # Parent selection section
            with Vertical(id="parent-section"):
                with Vertical(id="parent1-section"):
                    yield Static("👤 Parent 1", classes="parent-title")
                    yield Static("[Press 1 or click to select]", id="parent1-info", classes="parent-info")
                    yield Button("Select Parent 1 [1]", id="select-parent1")

                with Vertical(id="parent2-section"):
                    yield Static("👤 Parent 2", classes="parent-title")
                    yield Static("[Press 2 or click to select]", id="parent2-info", classes="parent-info")
                    yield Button("Select Parent 2 [2]", id="select-parent2")

            # Content mode selection
            yield Static("Content Mode:")
            yield Select(
                [
                    ("Auto (inherit from parents)", "auto"),
                    ("SFW", "SFW"),
                    ("NSFW", "NSFW"),
                    ("Platform-Safe", "Platform-Safe"),
                ],
                value="auto",
                id="mode",
            )
            
            yield Static("Template:")
            yield Select([], id="template")

            with Vertical(classes="button-row"):
                yield Button("▶️  [Enter] Generate Offspring", id="generate", variant="primary", disabled=True)
                yield Button("⬅️  [Q] Back", id="back")

            yield Static("Output:")
            yield RichLog(id="output-log", highlight=True, markup=True, auto_scroll=True)

            yield Static("", id="status", classes="status")
        yield Footer()
        
    def on_mount(self) -> None:
        """Load templates when screen is mounted."""
        self.load_templates()

    def load_templates(self) -> None:
        """Load templates into the select widget."""
        from bpui.features.templates.templates import TemplateManager
        template_select = self.query_one("#template", Select)
        
        try:
            manager = TemplateManager()
            self.templates = manager.list_templates()
            
            options = []
            default_template_name = None
            for template in self.templates:
                label = f"{template.name} ({len(template.assets)} assets)"
                if template.is_official:
                    label += " ★"
                    if not default_template_name:
                        default_template_name = template.name
                options.append((label, template.name))
            
            template_select.set_options(options)
            
            if default_template_name:
                template_select.value = default_template_name
                
        except Exception as e:
            template_select.set_options([ (f"Error: {e}", None) ])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            if not self.is_generating:
                self.app.pop_screen()
        elif event.button.id == "select-parent1":
            await self.select_parent(1)
        elif event.button.id == "select-parent2":
            await self.select_parent(2)
        elif event.button.id == "generate":
            if self.parent1_path and self.parent2_path:
                await self.generate_offspring()
    
    async def select_parent(self, parent_num: int) -> None:
        """Show parent selection dialog."""
        self.app.push_screen(ParentSelectScreen(parent_num, self))
    
    def set_parent(self, parent_num: int, draft_path, assets: dict) -> None:
        """Set parent character after selection."""
        from bpui.utils.metadata.metadata import DraftMetadata
        
        metadata = DraftMetadata.load(draft_path)
        char_name = metadata.character_name if metadata else draft_path.name
        
        if parent_num == 1:
            self.parent1_path = draft_path
            self.parent1_assets = assets
            self.parent1_name = char_name
            
            # Update display
            info = self.query_one("#parent1-info", Static)
            info.update(f"[bold green]✓ Selected:[/bold green]\n\n{char_name}\n{draft_path.name}")
            info.add_class("selected-parent")
        else:
            self.parent2_path = draft_path
            self.parent2_assets = assets
            self.parent2_name = char_name
            
            # Update display
            info = self.query_one("#parent2-info", Static)
            info.update(f"[bold green]✓ Selected:[/bold green]\n\n{char_name}\n{draft_path.name}")
            info.add_class("selected-parent")
        
        # Enable generate button if both parents selected
        generate_button = self.query_one("#generate", Button)
        generate_button.disabled = not (self.parent1_path and self.parent2_path)
    
    async def generate_offspring(self) -> None:
        """Generate offspring character."""
        if self.is_generating:
            return

        status = self.query_one("#status", Static)
        output_log = self.query_one("#output-log", RichLog)
        
        output_log.clear()
        output_log.write("[bold cyan]Initializing offspring generation...[/]")
        output_log.refresh()
        
        status.update("⏳ Generating offspring...")
        status.remove_class("error")
        status.refresh()

        self.is_generating = True

        try:
            output_log.write("[dim]Importing modules...[/dim]")
            output_log.refresh()
            
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            from ..prompting import build_offspring_prompt, build_asset_prompt
            from ..parse_blocks import extract_single_asset, extract_character_name
            from bpui.utils.file_io.pack_io import create_draft_dir
            from bpui.utils.topological_sort import topological_sort
            from pathlib import Path

            output_log.write("[dim]Modules imported ✓[/dim]")
            output_log.refresh()
            
            # Get content mode
            mode_select = self.query_one("#mode", Select)
            mode_value = mode_select.value
            mode = None if mode_value == "auto" or mode_value is None else str(mode_value)
            
            # Get template
            template_select = self.query_one("#template", Select)
            template_name = template_select.value
            if not template_name:
                status.update("✗ Please select a template")
                status.add_class("error")
                self.is_generating = False
                return
            
            template = next((t for t in self.templates if t.name == template_name), None)
            if not template:
                status.update(f"✗ Template '{template_name}' not found")
                status.add_class("error")
                self.is_generating = False
                return
                
            try:
                asset_order = topological_sort(template.assets)
            except ValueError as e:
                status.update(f"✗ Template error: {e}")
                status.add_class("error")
                self.is_generating = False
                return

            output_log.write(f"\n[bold cyan]Parents:[/]")
            output_log.write(f"[bold cyan]  Parent 1:[/] {self.parent1_name}")
            output_log.write(f"[bold cyan]  Parent 2:[/] {self.parent2_name}")
            output_log.write(f"[bold cyan]  Mode:[/] {mode or 'Auto'}")
            output_log.write(f"[bold cyan]  Template:[/] {template.name}")
            output_log.write(f"[bold cyan]  Model:[/] {self.config.model}")
            output_log.refresh()
            
            # Check API key
            if not self.config.api_key:
                output_log.write("\n[bold red]✗ No API key found![/]")
                output_log.write("[dim]Configure API key in Settings screen[/dim]")
                status.update("✗ No API key configured")
                status.add_class("error")
                self.is_generating = False
                return
            
            output_log.write("[dim]  API key: configured ✓[/dim]")
            output_log.write("\n[bold cyan]Step 1: Generating offspring seed...[/]\n")
            output_log.refresh()

            # Step 1: Generate offspring seed
            engine_config = {
                "model": self.config.model,
                "api_key": self.config.api_key,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }

            if self.config.engine == "litellm":
                engine = LiteLLMEngine(**engine_config)
            else:
                engine_config["base_url"] = self.config.base_url
                engine = OpenAICompatEngine(**engine_config)

            # Build offspring prompt
            system_prompt, user_prompt = build_offspring_prompt(
                parent1_assets=self.parent1_assets,
                parent2_assets=self.parent2_assets,
                parent1_name=self.parent1_name or "Parent 1",
                parent2_name=self.parent2_name or "Parent 2",
                mode=mode
            )

            output_log.write("[dim]Sending parents to LLM...[/dim]")
            output_log.refresh()

            # Stream seed generation
            raw_output = ""
            import asyncio
            timeout_seconds = 300
            
            async def stream_with_timeout():
                nonlocal raw_output
                stream = engine.generate_stream(system_prompt, user_prompt)
                async for chunk in stream:
                    raw_output += chunk
                    output_log.write(chunk)
                    output_log.refresh()
            
            try:
                await asyncio.wait_for(stream_with_timeout(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                output_log.write(f"\n[bold red]✗ Timeout after {timeout_seconds}s[/]")
                raise

            # Extract seed from output
            offspring_seed = raw_output.strip()
            if not offspring_seed:
                raise ValueError("No seed generated")
            
            output_log.write(f"\n\n[bold green]✓ Offspring seed generated:[/]")
            output_log.write(f"  {offspring_seed[:200]}{'...' if len(offspring_seed) > 200 else ''}")
            output_log.refresh()

            # Step 2: Generate full character suite using orchestrator
            output_log.write("\n[bold cyan]Step 2: Generating full character suite...[/]\n")
            output_log.refresh()

            assets = {}
            character_name = None

            for asset_name in asset_order:
                output_log.write(f"\n[bold yellow]→ Generating {asset_name}...[/]")
                output_log.refresh()
                status.update(f"Generating {asset_name}...")
                status.refresh()

                # Build prompt with prior assets
                system_prompt, user_prompt = build_asset_prompt(
                    asset_name, offspring_seed, mode, assets
                )

                # Stream generation
                raw_output = ""
                chunk_count = 0
                
                async def asset_stream_with_timeout():
                    nonlocal raw_output, chunk_count
                    stream = engine.generate_stream(system_prompt, user_prompt)
                    async for chunk in stream:
                        raw_output += chunk
                        chunk_count += 1
                        if chunk_count % 10 == 0:
                            output_log.write(chunk)
                            output_log.refresh()
                        else:
                            output_log.write(chunk)
                    output_log.refresh()
                
                try:
                    await asyncio.wait_for(asset_stream_with_timeout(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    output_log.write(f"\n[bold red]✗ Timeout after {timeout_seconds}s[/]")
                    raise

                # Parse asset
                try:
                    asset_content = extract_single_asset(raw_output, asset_name)
                    assets[asset_name] = asset_content
                    output_log.write(f"\n[bold green]✓ {asset_name} complete ({len(asset_content)} chars)[/]")
                    output_log.refresh()

                    if asset_name == "character_sheet" and not character_name:
                        character_name = extract_character_name(asset_content)
                        if character_name:
                            output_log.write(f"[bold cyan]Character:[/] {character_name}")
                            output_log.refresh()

                except Exception as e:
                    output_log.write(f"\n[bold red]✗ Failed to parse {asset_name}: {e}[/]")
                    raise

            if not character_name:
                character_name = "offspring_character"

            output_log.write("\n\n[bold green]✓ All assets generated![/]")
            output_log.write(f"[bold green]✓ Generated {len(assets)} assets[/]")
            output_log.refresh()

            # Save draft with lineage metadata
            drafts_root = Path.cwd() / "drafts"
            
            # Get relative paths for parents
            drafts_root_abs = drafts_root.resolve()
            parent1_rel = str(self.parent1_path.relative_to(drafts_root_abs)) if self.parent1_path else ""
            parent2_rel = str(self.parent2_path.relative_to(drafts_root_abs)) if self.parent2_path else ""
            
            # Create draft
            draft_dir = create_draft_dir(
                assets, 
                character_name,
                seed=offspring_seed,
                mode=mode or None,
                model=self.config.model
            )
            
            # Update metadata with lineage info
            from bpui.utils.metadata.metadata import DraftMetadata
            metadata = DraftMetadata.load(draft_dir)
            if metadata:
                metadata.parent_drafts = [parent1_rel, parent2_rel]
                metadata.offspring_type = "generated"  # Could be inferred from analysis later
                metadata.save(draft_dir)
            
            output_log.write(f"[bold green]✓ Draft saved:[/] {draft_dir}")
            output_log.write(f"[bold green]✓ Lineage tracked:[/] {parent1_rel} + {parent2_rel}")
            output_log.refresh()

            status.update("✓ Offspring generation complete!")
            status.refresh()

            # Navigate to review screen
            from .review import ReviewScreen
            self.app.push_screen(ReviewScreen(
                self.config, 
                draft_dir, 
                assets,
                seed=offspring_seed,
                mode=mode if mode is not None else "Auto",
                model=self.config.model,
                template=template
            ))

        except Exception as e:
            output_log.write(f"\n[bold red]✗ Error: {e}[/]")
            status.update(f"✗ Error: {e}")
            status.add_class("error")

        finally:
            self.is_generating = False
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        if not self.is_generating:
            self.app.pop_screen()
    
    def action_select_parent1(self) -> None:
        """Select parent 1 (1 key)."""
        if not self.is_generating:
            self.run_worker(lambda: self.select_parent(1), exclusive=False)
    
    def action_select_parent2(self) -> None:
        """Select parent 2 (2 key)."""
        if not self.is_generating:
            self.run_worker(lambda: self.select_parent(2), exclusive=False)
    
    def action_start_offspring(self) -> None:
        """Start generation (Enter key)."""
        if not self.is_generating and self.parent1_path and self.parent2_path:
            generate_button = self.query_one("#generate", Button)
            self.post_message(Button.Pressed(generate_button))
    
    def action_cancel_generation(self) -> None:
        """Cancel ongoing generation."""
        if self.is_generating:
            self.is_generating = False
            status = self.query_one("#status", Static)
            status.update("⚠️  Cancelled by user")


class ParentSelectScreen(Screen):
    """Parent selection dialog."""
    
    BINDINGS = [
        ("escape,q", "cancel", "Cancel"),
        ("enter", "confirm", "Select"),
        ("f", "focus_search", "Search"),
    ]
    
    def __init__(self, parent_num: int, offspring_screen: OffspringScreen):
        super().__init__()
        self.parent_num = parent_num
        self.offspring_screen = offspring_screen
        self.drafts = []
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"👤 Select Parent {self.parent_num}", id="title")
            yield Input(placeholder="🔍 Search drafts...", id="search-input")
            yield ListView(id="drafts-list")
            with Horizontal(id="buttons"):
                yield Button("✓ [Enter] Select", id="confirm", variant="primary")
                yield Button("[Q] Cancel", id="cancel")
    
    async def on_mount(self) -> None:
        """Load drafts list."""
        await self.load_drafts()
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input change."""
        if event.input.id == "search-input":
            await self.apply_filter(event.value)
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in search input."""
        drafts_list = self.query_one("#drafts-list", ListView)
        if drafts_list.index is not None and self.drafts:
            idx = drafts_list.index
            if 0 <= idx < len(self.drafts):
                await self.select_draft(self.drafts[idx][0])
    
    async def load_drafts(self) -> None:
        """Load all drafts."""
        from bpui.utils.metadata.metadata import search_metadata
        from pathlib import Path
        
        drafts_dir = Path.cwd() / "drafts"
        self.drafts = search_metadata(drafts_dir)
        
        await self.apply_filter("")
    
    async def apply_filter(self, query: str) -> None:
        """Apply search filter."""
        from bpui.utils.metadata.metadata import search_metadata
        from pathlib import Path
        
        drafts_dir = Path.cwd() / "drafts"
        filtered = search_metadata(drafts_dir, query=query)
        
        drafts_list = self.query_one("#drafts-list", ListView)
        await drafts_list.clear()
        
        if not filtered:
            await drafts_list.append(ListItem(Static("[No matches]")))
            return
        
        for draft_path, metadata in filtered:
            char_name = metadata.character_name or draft_path.name
            display = f"{char_name} ({metadata.mode or 'Auto'})"
            await drafts_list.append(ListItem(Static(display)))
        
        self.drafts = filtered
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle draft selection."""
        if event.item and self.drafts:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.drafts):
                await self.select_draft(self.drafts[idx][0])
    
    async def select_draft(self, draft_path) -> None:
        """Select a draft as parent."""
        from bpui.utils.file_io.pack_io import load_draft
        
        try:
            assets = load_draft(draft_path)
            self.offspring_screen.set_parent(self.parent_num, draft_path, assets)
            self.app.pop_screen()
        except Exception as e:
            # Show error
            status = self.query_one("#title", Static)
            status.update(f"✗ Error loading draft: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm":
            self.action_confirm()
        else:
            self.action_cancel()
    
    def action_confirm(self) -> None:
        """Confirm selection (Enter key)."""
        drafts_list = self.query_one("#drafts-list", ListView)
        if drafts_list.index is not None and self.drafts:
            idx = drafts_list.index
            if 0 <= idx < len(self.drafts):
                self.run_worker(lambda: self.select_draft(self.drafts[idx][0]), exclusive=False)
    
    def action_cancel(self) -> None:
        """Cancel (Q key)."""
        self.app.pop_screen()
    
    def action_focus_search(self) -> None:
        """Focus search input (F key)."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()