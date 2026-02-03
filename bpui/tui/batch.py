"""Batch compilation screen for Blueprint UI."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, Input, Select, RichLog, ProgressBar, Footer
from textual.worker import Worker, WorkerState


class BatchScreen(Screen):
    """Batch compile multiple seeds screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("ctrl+c", "cancel_batch", "Cancel"),
        ("l", "load_seeds", "Load"),
        ("enter", "start_batch", "Start"),
    ]

    CSS = """
    BatchScreen {
        layout: vertical;
    }

    #batch-container {
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

    .form-row {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .form-row Static {
        width: 20;
        content-align: right middle;
        margin-right: 2;
    }

    .form-row Input {
        width: 1fr;
    }

    .form-row Select {
        width: 1fr;
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

    #progress-container {
        height: auto;
        margin-bottom: 1;
        border: solid $primary;
        padding: 1;
    }

    #progress-bar {
        width: 100%;
        margin-bottom: 1;
    }

    #status {
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #log {
        height: 1fr;
        border: solid $primary;
    }

    .error {
        color: $error;
    }

    .success {
        color: $success;
    }
    """

    def __init__(self, config):
        """Initialize batch screen."""
        super().__init__()
        self.config = config
        self.seeds = []
        self.current_index = 0
        self.failed_seeds = []
        self.batch_running = False

    def compose(self) -> ComposeResult:
        """Compose the batch screen layout."""
        with Container(id="batch-container"):
            yield Static("📦 Batch Compilation", classes="title")

            # File input
            with Vertical(classes="form-row"):
                yield Static("Seed File:")
                yield Input(
                    placeholder="Path to file with seeds (one per line)",
                    id="seed-file",
                )

            # Mode selection
            with Vertical(classes="form-row"):
                yield Static("Content Mode:")
                yield Select(
                    [
                        ("Auto (infer from seed)", "auto"),
                        ("SFW", "sfw"),
                        ("NSFW", "nsfw"),
                        ("Platform-Safe", "platform-safe"),
                    ],
                    value="auto",
                    id="mode",
                )

            # Action buttons
            with Vertical(classes="button-row"):
                yield Button("[L] Load Seeds", id="load", variant="primary")
                yield Button("[Enter] Start Batch", id="start", variant="success", disabled=True)
                yield Button("[Ctrl+C] Cancel", id="cancel", variant="error", disabled=True)
                yield Button("🏠 [Q] Home", id="home")

            # Progress section
            with Vertical(id="progress-container"):
                yield ProgressBar(id="progress-bar", total=100, show_eta=False)
                yield Static("Ready", id="status")

            # Log output
            yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "home":
            if self.batch_running:
                status = self.query_one("#status", Static)
                status.update("⚠️  Batch operation in progress! Wait or cancel first.")
                status.add_class("error")
                return
            
            from .home import HomeScreen
            self.app.switch_screen(HomeScreen(self.config))

        elif event.button.id == "load":
            await self.load_seeds()

        elif event.button.id == "start":
            await self.start_batch()

        elif event.button.id == "cancel":
            await self.cancel_batch()

    async def load_seeds(self) -> None:
        """Load seeds from file."""
        seed_file_input = self.query_one("#seed-file", Input)
        log = self.query_one("#log", RichLog)
        status = self.query_one("#status", Static)
        start_button = self.query_one("#start", Button)

        file_path = Path(seed_file_input.value.strip())

        if not file_path.exists():
            log.write(f"[bold red]✗ File not found: {file_path}[/bold red]")
            status.update("File not found")
            status.add_class("error")
            return

        try:
            seeds_raw = file_path.read_text().strip().split("\n")
            self.seeds = [s.strip() for s in seeds_raw if s.strip()]

            if not self.seeds:
                log.write("[bold red]✗ No seeds found in file[/bold red]")
                status.update("No seeds found")
                status.add_class("error")
                return

            log.write(f"[bold green]✓ Loaded {len(self.seeds)} seeds[/bold green]")
            for i, seed in enumerate(self.seeds, 1):
                log.write(f"  {i}. {seed[:80]}{'...' if len(seed) > 80 else ''}")

            status.update(f"Ready: {len(self.seeds)} seeds loaded")
            status.remove_class("error")
            status.add_class("success")
            start_button.disabled = False

        except Exception as e:
            log.write(f"[bold red]✗ Error loading file: {e}[/bold red]")
            status.update(f"Error: {e}")
            status.add_class("error")

    async def start_batch(self) -> None:
        """Start batch compilation."""
        if not self.seeds:
            return

        self.batch_running = True
        self.current_index = 0
        self.failed_seeds = []

        # Disable/enable buttons
        load_button = self.query_one("#load", Button)
        start_button = self.query_one("#start", Button)
        cancel_button = self.query_one("#cancel", Button)
        
        load_button.disabled = True
        start_button.disabled = True
        cancel_button.disabled = False

        # Setup progress bar
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(total=len(self.seeds), progress=0)

        log = self.query_one("#log", RichLog)
        log.write("\n[bold cyan]═══ Starting Batch Compilation ═══[/bold cyan]\n")

        # Start worker
        self.run_worker(self.compile_all_seeds, exclusive=True, name="batch_compile")

    async def compile_all_seeds(self) -> None:
        """Compile all seeds in sequence."""
        from ..prompting import build_orchestrator_prompt
        from ..parse_blocks import parse_blueprint_output, extract_character_name
        from ..pack_io import create_draft_dir
        
        log = self.query_one("#log", RichLog)
        status = self.query_one("#status", Static)
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        mode_select = self.query_one("#mode", Select)
        
        mode = mode_select.value
        # Convert mode to string or None for build_orchestrator_prompt
        mode_param: str | None = None
        if mode and mode != "auto":
            mode_param = str(mode)
        
        mode_str = mode_param or "Auto"

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
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

        for i, seed in enumerate(self.seeds):
            if not self.batch_running:
                log.write("\n[bold yellow]⚠️  Batch cancelled by user[/bold yellow]")
                break

            self.current_index = i
            log.write(f"\n[bold cyan]─── Seed {i+1}/{len(self.seeds)} ───[/bold cyan]")
            log.write(f"[dim]Seed: {seed}[/dim]")
            status.update(f"Compiling {i+1}/{len(self.seeds)}: {seed[:50]}...")

            try:
                # Build prompt
                system_prompt, user_prompt = build_orchestrator_prompt(
                    seed, 
                    mode_param
                )

                # Compile with streaming
                output = ""
                async for chunk in engine.generate_stream(system_prompt, user_prompt):
                    output += chunk
                    if not self.batch_running:
                        break

                if not self.batch_running:
                    break

                # Parse output
                assets = parse_blueprint_output(output)

                # Extract character name
                character_name = extract_character_name(assets.get("character_sheet", ""))
                if not character_name:
                    character_name = f"character_{i+1:03d}"

                # Save pack
                draft_dir = create_draft_dir(assets, character_name)
                log.write(f"[green]✓ Saved to {draft_dir.name}[/green]")

            except Exception as e:
                log.write(f"[bold red]✗ Failed: {e}[/bold red]")
                self.failed_seeds.append((seed, str(e)))

            # Update progress
            progress_bar.update(progress=i+1)

        # Summary
        log.write("\n[bold cyan]═══ Batch Complete ═══[/bold cyan]")
        successful = len(self.seeds) - len(self.failed_seeds)
        log.write(f"[green]✓ Successful: {successful}/{len(self.seeds)}[/green]")
        
        if self.failed_seeds:
            log.write(f"[red]✗ Failed: {len(self.failed_seeds)}[/red]")
            for seed, error in self.failed_seeds:
                log.write(f"  • {seed[:60]}... → {error}")

        status.update(f"Complete: {successful}/{len(self.seeds)} successful")
        status.remove_class("error")
        status.add_class("success")

        # Re-enable buttons
        self.batch_running = False
        load_button = self.query_one("#load", Button)
        start_button = self.query_one("#start", Button)
        cancel_button = self.query_one("#cancel", Button)
        
        load_button.disabled = False
        start_button.disabled = False
        cancel_button.disabled = True

    async def cancel_batch(self) -> None:
        """Cancel batch operation."""
        self.batch_running = False
        cancel_button = self.query_one("#cancel", Button)
        cancel_button.disabled = True
        
        status = self.query_one("#status", Static)
        status.update("Cancelling...")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        if not self.batch_running:
            from .home import HomeScreen
            self.app.switch_screen(HomeScreen(self.config))
    
    def action_cancel_batch(self) -> None:
        """Cancel ongoing batch (Ctrl+C)."""
        if self.batch_running:
            self.run_worker(self.cancel_batch, exclusive=False)
    
    def action_load_seeds(self) -> None:
        """Load seeds from file (L key)."""
        if not self.batch_running:
            self.run_worker(self.load_seeds, exclusive=False)
    
    def action_start_batch(self) -> None:
        """Start batch compilation (Enter key)."""
        start_button = self.query_one("#start", Button)
        if not start_button.disabled and not self.batch_running:
            self.run_worker(self.start_batch, exclusive=False)
