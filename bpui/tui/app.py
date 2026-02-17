"""Blueprint UI - Main TUI application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from .home import HomeScreen
from .settings import SettingsScreen
from .seed_generator import SeedGeneratorScreen
from .compile import CompileScreen
from .review import ReviewScreen
from .theme import TUIThemeManager
from bpui.core.config import Config


class BlueprintUI(App):
    """Blueprint UI Terminal Application."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "home", "Home"),
    ]
    
    # CSS will be loaded dynamically
    CSS = ""

    def __init__(self, config_path=None):
        """Initialize app."""
        super().__init__()
        self.config = Config(config_path)
        self.theme_manager = TUIThemeManager(self.config)
        self.title = "Blueprint UI - RPBotGenerator"
        self.sub_title = "Character Compilation System"
        
        # Load initial CSS
        self._reload_theme_css()
    
    def _reload_theme_css(self) -> None:
        """Reload CSS from theme manager."""
        try:
            css_content = self.theme_manager.load_css()
            # Set CSS on the class, not instance
            type(self).CSS = css_content
        except FileNotFoundError as e:
            # Fall back to minimal CSS if theme file missing
            type(self).CSS = """
            Screen {
                background: $surface;
            }
            """
            print(f"Warning: {e}")

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
