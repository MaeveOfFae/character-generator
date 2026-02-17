"""Seed generator screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, TextArea, Static, Label, ListView, ListItem, Footer


class SeedGeneratorScreen(Screen):
    """Seed generator screen."""
    
    BINDINGS = [
        ("escape,q", "go_back", "Back"),
        ("enter", "generate_seeds", "Generate"),
        ("ctrl+s", "save_output", "Save Output"),
    ]

    def __init__(self, config):
        """Initialize seed generator screen."""
        super().__init__()
        self.config = config
        self.seeds = []

    def compose(self) -> ComposeResult:
        """Compose seed generator screen."""
        with Container(id="seed-gen-container"):
            yield Static("🎲 Seed Generator", classes="title")

            yield Label("Genre/Theme Lines (one per line):")
            yield TextArea(
                "Noir detective\nCyberpunk mercenary\nFantasy sorceress",
                id="genre-input",
            )

            with Vertical(classes="button-row"):
                yield Button("✨ [Enter] Generate Seeds", id="generate", variant="primary")
                yield Button("⬅️  [Q] Back", id="back")

            yield Label("Generated Seeds:")
            yield ListView(id="seeds-list")

            yield Static("", id="status", classes="status")
            yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "generate":
            await self.generate_seeds()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle seed selection."""
        if event.item and self.seeds:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.seeds):
                seed_text = self.seeds[idx]
                # Navigate to compile screen with this seed
                from .compile import CompileScreen
                self.app.push_screen(CompileScreen(self.config, initial_seed=seed_text))

    async def generate_seeds(self) -> None:
        """Generate seeds from genre input."""
        status = self.query_one("#status", Static)
        status.update("⏳ Generating seeds...")
        status.remove_class("error")

        try:
            from ..llm.litellm_engine import LiteLLMEngine
            from ..llm.openai_compat_engine import OpenAICompatEngine
            from ..prompting import build_seedgen_prompt

            genre_input = self.query_one("#genre-input", TextArea)
            genre_lines = genre_input.text

            if not genre_lines.strip():
                status.update("✗ Please enter genre/theme lines")
                status.add_class("error")
                return

            # Build prompt
            system_prompt, user_prompt = build_seedgen_prompt(genre_lines)

            # Create engine
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

            # Generate
            output = await engine.generate(system_prompt, user_prompt)

            # Parse seeds (one per line, skip empty)
            self.seeds = [
                line.strip()
                for line in output.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]

            # Update list
            seeds_list = self.query_one("#seeds-list", ListView)
            await seeds_list.clear()
            for seed in self.seeds:
                await seeds_list.append(ListItem(Static(seed)))

            status.update(f"✓ Generated {len(self.seeds)} seeds")

        except Exception as e:
            status.update(f"✗ Error: {e}")
            status.add_class("error")
    
    def action_go_back(self) -> None:
        """Go back to home screen."""
        from .home import HomeScreen
        self.app.switch_screen(HomeScreen(self.config))
    
    def action_generate_seeds(self) -> None:
        """Generate seeds (Enter key)."""
        self.run_worker(self.generate_seeds, exclusive=False)
    
    def action_save_output(self) -> None:
        """Save seeds output (Ctrl+S)."""
        if not self.seeds:
            status = self.query_one("#status", Static)
            status.update("No seeds to save")
            return
        
        # TODO: Implement save-to-file dialog
        status = self.query_one("#status", Static)
        status.update("Save functionality coming soon...")
