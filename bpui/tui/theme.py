"""TUI theme management for Textual application."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App
    from bpui.core.config import Config


class TUIThemeManager:
    """Manages TUI theme loading and application."""
    
    def __init__(self, config: "Config"):
        """Initialize theme manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self._theme_name = config.theme_name
    
    def get_css_path(self) -> Path:
        """Get path to active theme CSS file.
        
        Returns:
            Path to .tcss file for active theme
            
        Raises:
            FileNotFoundError: If theme file doesn't exist
        """
        # Get project root (bpui/tui/theme.py -> ../../resources/themes/)
        project_root = Path(__file__).parent.parent.parent
        themes_dir = project_root / "resources" / "themes"
        
        theme_file = themes_dir / f"{self._theme_name}.tcss"
        
        if not theme_file.exists():
            # Fall back to dark theme if custom theme not found
            theme_file = themes_dir / "dark.tcss"
            if not theme_file.exists():
                raise FileNotFoundError(
                    f"Theme file not found: {theme_file}\n"
                    f"Themes directory: {themes_dir}"
                )
        
        return theme_file
    
    def load_css(self) -> str:
        """Load CSS content from active theme file.
        
        Returns:
            CSS content as string
        """
        css_path = self.get_css_path()
        return css_path.read_text(encoding="utf-8")
    
    def reload_theme(self) -> None:
        """Reload theme from config (for live theme switching)."""
        self._theme_name = self.config.theme_name
    
    @property
    def theme_name(self) -> str:
        """Get current theme name."""
        return self._theme_name
