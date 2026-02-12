"""Home screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static, Footer


class HomeScreen(Screen):
    """Home screen with main menu."""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "action_compile", "Compile"),
        ("2", "action_batch", "Batch"),
        ("3", "action_seed_gen", "Seed Gen"),
        ("4", "action_drafts", "Drafts"),
        ("5", "action_offspring", "Offspring"),
        ("6", "action_validate", "Validate"),
        ("7", "action_settings", "Settings"),
    ]

    CSS = """
    HomeScreen {
        align: center middle;
    }

    #home-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    .title {
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .subtitle {
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 2;
    }

    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self, config):
        """Initialize home screen."""
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose home screen."""
        with Container(id="home-container"):
            yield Static("🎭 Blueprint UI", classes="title")
            yield Static("RPBotGenerator Character Compiler", classes="subtitle")
            yield Button("🌱 [1] Compile from Seed", id="compile", variant="primary")
            yield Button("📦 [2] Batch Compile", id="batch")
            yield Button("🎲 [3] Seed Generator", id="seed-gen")
            yield Button("📁 [4] Open Drafts", id="drafts")
            yield Button("👶 [5] Offspring Generator", id="offspring")
            yield Button("✓ [6] Validate Directory", id="validate")
            yield Button("⚙️  [7] Settings", id="settings")
            yield Button("❌ [Q] Quit", id="quit", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "compile":
            from .compile import CompileScreen
            self.app.push_screen(CompileScreen(self.config))
        elif event.button.id == "batch":
            from .batch import BatchScreen
            self.app.push_screen(BatchScreen(self.config))
        elif event.button.id == "seed-gen":
            from .seed_generator import SeedGeneratorScreen
            self.app.push_screen(SeedGeneratorScreen(self.config))
        elif event.button.id == "settings":
            from .settings import SettingsScreen
            self.app.push_screen(SettingsScreen(self.config))
        elif event.button.id == "drafts":
            from .drafts import DraftsScreen
            self.app.push_screen(DraftsScreen(self.config))
        elif event.button.id == "validate":
            from .validate_screen import ValidateScreen
            self.app.push_screen(ValidateScreen(self.config))
        elif event.button.id == "offspring":
            from .offspring import OffspringScreen
            self.app.push_screen(OffspringScreen(self.config))
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_compile(self) -> None:
        """Open compile screen."""
        from .compile import CompileScreen
        self.app.push_screen(CompileScreen(self.config))
    
    def action_batch(self) -> None:
        """Open batch compile screen."""
        from .batch import BatchScreen
        self.app.push_screen(BatchScreen(self.config))
    
    def action_seed_gen(self) -> None:
        """Open seed generator screen."""
        from .seed_generator import SeedGeneratorScreen
        self.app.push_screen(SeedGeneratorScreen(self.config))
    
    def action_drafts(self) -> None:
        """Open drafts screen."""
        from .drafts import DraftsScreen
        self.app.push_screen(DraftsScreen(self.config))
    
    def action_validate(self) -> None:
        """Open validate screen."""
        from .validate_screen import ValidateScreen
        self.app.push_screen(ValidateScreen(self.config))
    
    def action_settings(self) -> None:
        """Open settings screen."""
        from .settings import SettingsScreen
        self.app.push_screen(SettingsScreen(self.config))
    
    def action_offspring(self) -> None:
        """Open offspring generator screen."""
        from .offspring import OffspringScreen
        self.app.push_screen(OffspringScreen(self.config))
