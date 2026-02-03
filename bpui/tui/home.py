"""Home screen for Blueprint UI."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static


class HomeScreen(Screen):
    """Home screen with main menu."""

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
            yield Button("🌱 Compile from Seed", id="compile", variant="primary")
            yield Button("🎲 Seed Generator", id="seed-gen")
            yield Button("📁 Open Drafts", id="drafts")
            yield Button("✓ Validate Directory", id="validate")
            yield Button("⚙️  Settings", id="settings")
            yield Button("❌ Quit", id="quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "compile":
            from .compile import CompileScreen
            self.app.push_screen(CompileScreen(self.config))
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
