"""Blueprint UI - Main TUI application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from .home import HomeScreen
from .settings import SettingsScreen
from .seed_generator import SeedGeneratorScreen
from .compile import CompileScreen
from .review import ReviewScreen
from bpui.core.config import Config


class BlueprintUI(App):
    """Blueprint UI Terminal Application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "home", "Home"),
    ]

    def __init__(self, config_path=None):
        """Initialize app."""
        super().__init__()
        self.config = Config(config_path)
        self.title = "Blueprint UI - RPBotGenerator"
        self.sub_title = "Character Compilation System"

    def compose(self) -> ComposeResult:
        """Compose app layout."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self.push_screen(HomeScreen(self.config))

    def action_home(self) -> None:
        """Go to home screen."""
        self.push_screen(HomeScreen(self.config))
