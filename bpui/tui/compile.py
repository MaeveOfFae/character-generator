"""Compile screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static, Label, RichLog, Footer
from textual.worker import Worker, WorkerState


class CompileScreen(Screen):
    """Compilation screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("ctrl+c", "cancel_generation", "Cancel"),
        ("enter", "start_compile", "Compile"),
    ]

    CSS = """
    CompileScreen {
        layout: vertical;
    }

    #compile-container {
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

    .field-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    Input, Select {
        width: 100%;
        margin-bottom: 1;
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

    #output-log {
        height: 1fr;
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
    """

    def __init__(self, config, initial_seed=""):
        """Initialize compile screen."""
        super().__init__()
        self.config = config
        self.initial_seed = initial_seed
        self.output_text = ""
        self.is_generating = False

    def compose(self) -> ComposeResult:
        """Compose compile screen."""
        with Container(id="compile-container"):
            yield Static("🌱 Compile from Seed", classes="title")

            yield Label("Seed:", classes="field-label")
            yield Input(
                value=self.initial_seed,
                placeholder="e.g., Noir detective with psychic abilities",
                id="seed",
            )

            yield Label("Content Mode:", classes="field-label")
            yield Select(
                [
                    ("Auto (infer from seed)", "auto"),
                    ("SFW", "SFW"),
                    ("NSFW", "NSFW"),
                    ("Platform-Safe", "Platform-Safe"),
                ],
                value="auto",
                id="mode",
            )

            yield Label("Model Override (optional):", classes="field-label")
            yield Input(
                value="",
                placeholder="Leave empty to use config default",
                id="model-override",
            )

            with Vertical(classes="button-row"):
                yield Button("▶️  [Enter] Compile", id="compile", variant="primary")
                yield Button("⬅️  [Q] Back", id="back")

            yield Label("Output:")
            yield RichLog(id="output-log", highlight=True, markup=True, auto_scroll=True)

            yield Static("", id="status", classes="status")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            if not self.is_generating:
                self.app.pop_screen()

        elif event.button.id == "compile":
            # Show immediate feedback
            status = self.query_one("#status", Static)
            status.update("⏳ Starting compilation...")
            status.refresh()
            
            # Run compilation in background to avoid blocking UI
            self.run_worker(self.compile_character(), exclusive=True, name="compile")
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.worker.name == "compile":
            status = self.query_one("#status", Static)
            output_log = self.query_one("#output-log", RichLog)
            
            if event.state == WorkerState.ERROR:
                error = event.worker.error
                output_log.write(f"\n[bold red]✗ Worker error: {error}[/]")
                output_log.refresh()
                status.update(f"✗ Error: {error}")
                status.add_class("error")
                status.refresh()
                self.is_generating = False
            elif event.state == WorkerState.CANCELLED:
                output_log.write(f"\n[bold yellow]⚠ Compilation cancelled[/]")
                output_log.refresh()
                status.update("⚠ Cancelled")
                status.refresh()
                self.is_generating = False

    async def compile_character(self) -> None:
        """Compile character from seed."""
        if self.is_generating:
            return

        status = self.query_one("#status", Static)
        output_log = self.query_one("#output-log", RichLog)
        
        # Clear and show initial message
        output_log.clear()
        output_log.write("[bold cyan]Initializing compilation...[/]")
        output_log.refresh()
        
        status.update("⏳ Compiling character...")
        status.remove_class("error")
        status.refresh()

        self.is_generating = True

        try:
            output_log.write("[dim]Importing modules...[/dim]")
            output_log.refresh()
            
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            from ..prompting import build_asset_prompt
            from ..parse_blocks import extract_single_asset, extract_character_name, ASSET_ORDER
            from ..pack_io import create_draft_dir

            output_log.write("[dim]Modules imported ✓[/dim]")
            output_log.refresh()
            
            seed_input = self.query_one("#seed", Input)
            mode_select = self.query_one("#mode", Select)
            model_override = self.query_one("#model-override", Input)

            seed = seed_input.value.strip()
            if not seed:
                status.update("✗ Please enter a seed")
                status.add_class("error")
                status.refresh()
                self.is_generating = False
                return

            mode_value = mode_select.value
            mode = None if mode_value == "auto" or mode_value is None else str(mode_value)
            model = model_override.value.strip() or self.config.model

            output_log.write(f"\n[bold cyan]Configuration:[/]")
            output_log.write(f"[bold cyan]  Seed:[/] {seed}")
            output_log.write(f"[bold cyan]  Mode:[/] {mode or 'Auto'}")
            output_log.write(f"[bold cyan]  Model:[/] {model}")
            output_log.write(f"[bold cyan]  Engine:[/] {self.config.engine}")
            output_log.refresh()
            
            # Check API key availability
            if not self.config.api_key:
                output_log.write("\n[bold red]✗ No API key found![/]")
                output_log.write("[dim]Configure API key in Settings screen[/dim]")
                output_log.refresh()
                status.update("✗ No API key configured")
                status.add_class("error")
                status.refresh()
                self.is_generating = False
                return
            
            output_log.write("[dim]  API key: configured ✓[/dim]")
            output_log.write("\n[bold cyan]Starting sequential generation...[/]\n")
            output_log.refresh()

            # Create engine
            engine_config = {
                "model": model,
                "api_key": self.config.api_key,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }

            output_log.write("[dim]Creating LLM engine...[/dim]")
            output_log.refresh()

            if self.config.engine == "litellm":
                engine = LiteLLMEngine(**engine_config)
            else:
                engine_config["base_url"] = self.config.base_url
                engine = OpenAICompatEngine(**engine_config)
            
            output_log.write("[dim]Engine created successfully[/dim]")
            output_log.refresh()

            # Generate each asset sequentially
            assets = {}
            character_name = None

            for asset_name in ASSET_ORDER:
                output_log.write(f"\n[bold yellow]→ Generating {asset_name}...[/]")
                output_log.refresh()
                status.update(f"Generating {asset_name}...")
                status.refresh()

                # Build prompt with prior assets as context
                system_prompt, user_prompt = build_asset_prompt(
                    asset_name, seed, mode, assets
                )

                # Stream generation
                raw_output = ""
                chunk_count = 0
                try:
                    output_log.write(f"[dim]Sending request to LLM...[/dim]")
                    output_log.refresh()
                    
                    stream = engine.generate_stream(system_prompt, user_prompt)
                    
                    # Add timeout wrapper
                    import asyncio
                    timeout_seconds = 300  # 5 minutes max per asset
                    
                    async def stream_with_timeout():
                        nonlocal raw_output, chunk_count
                        async for chunk in stream:
                            raw_output += chunk
                            chunk_count += 1
                            
                            # Write and refresh every 10 chunks to show progress
                            if chunk_count % 10 == 0:
                                output_log.write(chunk)
                                output_log.refresh()
                            else:
                                output_log.write(chunk)
                        
                        # Final refresh to show all content
                        output_log.refresh()
                    
                    try:
                        await asyncio.wait_for(stream_with_timeout(), timeout=timeout_seconds)
                    except asyncio.TimeoutError:
                        output_log.write(f"\n[bold red]✗ Timeout after {timeout_seconds}s[/]")
                        output_log.refresh()
                        raise TimeoutError(f"Generation timeout after {timeout_seconds}s")
                    
                except Exception as stream_error:
                    output_log.write(f"\n[bold red]✗ Streaming error: {stream_error}[/]")
                    output_log.write(f"[dim]Error type: {type(stream_error).__name__}[/dim]")
                    output_log.refresh()
                    raise

                # Parse this asset
                try:
                    asset_content = extract_single_asset(raw_output, asset_name)
                    assets[asset_name] = asset_content
                    output_log.write(f"\n[bold green]✓ {asset_name} complete ({len(asset_content)} chars)[/]")
                    output_log.refresh()

                    # Extract character name from character_sheet once available
                    if asset_name == "character_sheet" and not character_name:
                        character_name = extract_character_name(asset_content)
                        if character_name:
                            output_log.write(f"[bold cyan]Character:[/] {character_name}")
                            output_log.refresh()

                except Exception as e:
                    output_log.write(f"\n[bold red]✗ Failed to parse {asset_name}: {e}[/]")
                    output_log.write(f"[dim]Raw output length: {len(raw_output)} chars[/dim]")
                    output_log.refresh()
                    raise

            if not character_name:
                character_name = "unnamed_character"

            output_log.write("\n\n[bold green]✓ All assets generated![/]")
            output_log.write(f"[bold green]✓ Generated {len(assets)} assets[/]")
            output_log.refresh()

            # Save draft
            draft_dir = create_draft_dir(assets, character_name)
            output_log.write(f"[bold green]✓ Draft saved:[/] {draft_dir}")
            output_log.refresh()

            status.update("✓ Compilation complete!")
            status.refresh()

            # Navigate to review screen
            from .review import ReviewScreen
            self.app.push_screen(ReviewScreen(self.config, draft_dir, assets))

        except Exception as e:
            output_log.write(f"\n[bold red]✗ Error: {e}[/]")
            output_log.refresh()
            status.update(f"✗ Error: {e}")
            status.add_class("error")
            status.refresh()

        finally:
            self.is_generating = False
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        if not self.is_generating:
            self.app.pop_screen()
    
    def action_cancel_generation(self) -> None:
        """Cancel ongoing generation."""
        if self.is_generating:
            self.is_generating = False
            status = self.query_one("#status", Static)
            status.update("⚠️  Cancelled by user")
    
    def action_start_compile(self) -> None:
        """Start compilation (Enter key)."""
        if not self.is_generating:
            # Trigger the compile button
            compile_button = self.query_one("#compile", Button)
            self.post_message(Button.Pressed(compile_button))
