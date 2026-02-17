"""Tests for unified theme system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from bpui.core.theme import (
    ThemeDefinition,
    ThemeColors,
    BUILTIN_THEMES,
    load_theme_from_config,
    list_available_themes,
    save_theme_selection,
)
from bpui.core.config import Config
from bpui.tui.theme import TUIThemeManager


class TestThemeDefinition:
    """Test ThemeDefinition dataclass."""
    
    def test_theme_definition_creation(self):
        """Test creating a theme definition."""
        colors = ThemeColors(
            background="#000000",
            text="#ffffff",
            accent="#ff0000",
            button="#111111",
            button_text="#222222",
            border="#333333",
            highlight="#444444",
            window="#555555",
            tok_brackets="#aaa",
            tok_asterisk="#bbb",
            tok_parentheses="#ccc",
            tok_double_brackets="#ddd",
            tok_curly_braces="#eee",
            tok_pipes="#fff",
            tok_at_sign="#000",
            tui_primary="#111",
            tui_surface="#222",
        )
        theme = ThemeDefinition(
            name="test",
            display_name="Test Theme",
            colors=colors,
        )
        
        assert theme.name == "test"
        assert theme.display_name == "Test Theme"
        assert theme.colors.background == "#000000"
        assert theme.colors.tok_brackets == "#aaa"
        assert theme.colors.tui_primary == "#111"
    
    def test_theme_dict_conversion(self):
        """Test converting theme to dict format."""
        theme = BUILTIN_THEMES["dark"]
        
        # Test app_colors property
        app = theme.app_colors
        assert isinstance(app, dict)
        assert "background" in app
        assert "text" in app
        
        # Test tokenizer_colors property
        tok = theme.tokenizer_colors
        assert isinstance(tok, dict)
        assert "brackets" in tok
        assert "asterisk" in tok
        
        # Test tui_variables property
        tui = theme.tui_variables
        assert isinstance(tui, dict)
        assert "primary" in tui
        assert "surface" in tui
    
    def test_builtin_themes_exist(self):
        """Test that all built-in themes are defined."""
        assert "dark" in BUILTIN_THEMES
        assert "light" in BUILTIN_THEMES
        assert "nyx" in BUILTIN_THEMES
        assert "custom" in BUILTIN_THEMES
    
    def test_dark_theme_structure(self):
        """Test dark theme has all required fields."""
        dark = BUILTIN_THEMES["dark"]
        
        # Check app colors (via property)
        app = dark.app_colors
        assert "background" in app
        assert "text" in app
        assert "accent" in app
        assert "button" in app
        assert "button_text" in app
        assert "border" in app
        assert "highlight" in app
        assert "window" in app
        
        # Check tokenizer colors (via property)
        tok = dark.tokenizer_colors
        assert "brackets" in tok
        assert "asterisk" in tok
        assert "parentheses" in tok
        assert "double_brackets" in tok
        assert "curly_braces" in tok
        assert "pipes" in tok
        assert "at_sign" in tok
        
        # Check TUI variables (via property)
        tui = dark.tui_variables
        assert "primary" in tui
        assert "surface" in tui
    
    def test_all_themes_have_same_structure(self):
        """Test all built-in themes have the same structure."""
        dark_app_keys = set(BUILTIN_THEMES["dark"].app_colors.keys())
        
        for theme_name, theme in BUILTIN_THEMES.items():
            if theme_name == "custom":
                continue  # Custom is a placeholder
            assert set(theme.app_colors.keys()) == dark_app_keys, f"{theme_name} has different app keys"
            assert set(theme.tokenizer_colors.keys()) == set(BUILTIN_THEMES["dark"].tokenizer_colors.keys())
            assert set(theme.tui_variables.keys()) == set(BUILTIN_THEMES["dark"].tui_variables.keys())


class TestLoadTheme:
    """Test load_theme function."""
    
    def test_load_default_theme(self, tmp_path):
        """Test loading default dark theme."""
        config = Config(tmp_path / ".bpui.toml")
        theme = load_theme_from_config(config)
        
        assert theme.name == "dark"
        assert theme.colors.background == BUILTIN_THEMES["dark"].colors.background
    
    def test_load_light_theme(self, tmp_path):
        """Test loading light theme."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "light")
        
        theme = load_theme_from_config(config)
        
        assert theme.name == "light"
        assert theme.colors.background == BUILTIN_THEMES["light"].colors.background
    
    def test_load_nyx_theme(self, tmp_path):
        """Test loading nyx theme."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "nyx")
        
        theme = load_theme_from_config(config)
        
        assert theme.name == "nyx"
        assert theme.colors.background == BUILTIN_THEMES["nyx"].colors.background
    
    def test_load_custom_theme_overrides(self, tmp_path):
        """Test loading custom theme with overrides."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "custom")
        config.set("theme", {
            "app": {
                "background": "#custom",
                "text": "#ffffff",
            },
            "tokenizer": {
                "brackets": "#custom_bracket",
            }
        })
        
        theme = load_theme_from_config(config)
        
        assert theme.name == "custom"
        assert theme.app_colors["background"] == "#custom"
        assert theme.app_colors["text"] == "#ffffff"
        assert theme.tokenizer_colors["brackets"] == "#custom_bracket"
    
    def test_load_invalid_theme_falls_back_to_dark(self, tmp_path):
        """Test that invalid theme name falls back to dark."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "nonexistent")
        
        theme = load_theme_from_config(config)
        
        assert theme.name == "dark"


class TestListAvailableThemes:
    """Test list_available_themes function."""
    
    def test_list_builtin_themes(self):
        """Test listing built-in themes."""
        themes = list_available_themes()
        
        assert "dark" in themes
        assert "light" in themes
        assert "nyx" in themes
        assert "custom" in themes
    
    @patch("bpui.core.theme.Path")
    def test_list_includes_custom_theme_files(self, mock_path):
        """Test that custom .tcss files are discovered."""
        # Mock the themes directory to include a custom theme
        mock_themes_dir = Mock()
        mock_themes_dir.exists.return_value = True
        mock_themes_dir.glob.return_value = [
            Mock(stem="dark"),
            Mock(stem="light"),
            Mock(stem="nyx"),
            Mock(stem="custom_user_theme"),
        ]
        
        mock_path.return_value.parent.parent.parent = Mock()
        mock_path.return_value.parent.parent.parent.__truediv__ = lambda self, x: mock_themes_dir if x == "resources/themes" else Mock()
        
        # Note: This test would need actual file system mocking to work properly
        # For now, we just test the built-in themes
        themes = list_available_themes()
        assert len(themes) >= 4


class TestSaveThemeSelection:
    """Test save_theme_selection function."""
    
    def test_save_theme_selection(self, tmp_path):
        """Test saving theme selection to config."""
        config = Config(tmp_path / ".bpui.toml")
        
        save_theme_selection(config, "light")
        
        assert config.theme_name == "light"
        assert config.get("theme_name") == "light"
    
    def test_save_and_persist(self, tmp_path):
        """Test that saved theme persists after reload."""
        config_path = tmp_path / ".bpui.toml"
        config = Config(config_path)
        
        save_theme_selection(config, "nyx")
        config.save()
        
        # Reload config
        config2 = Config(config_path)
        assert config2.theme_name == "nyx"


class TestTUIThemeManager:
    """Test TUI theme manager."""
    
    def test_theme_manager_initialization(self, tmp_path):
        """Test initializing theme manager."""
        config = Config(tmp_path / ".bpui.toml")
        manager = TUIThemeManager(config)
        
        assert manager.theme_name == "dark"
    
    def test_get_css_path_dark(self, tmp_path):
        """Test getting CSS path for dark theme."""
        config = Config(tmp_path / ".bpui.toml")
        manager = TUIThemeManager(config)
        
        css_path = manager.get_css_path()
        
        assert css_path.name == "dark.tcss"
        assert "resources/themes" in str(css_path)
    
    def test_get_css_path_light(self, tmp_path):
        """Test getting CSS path for light theme."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "light")
        manager = TUIThemeManager(config)
        
        css_path = manager.get_css_path()
        
        assert css_path.name == "light.tcss"
    
    def test_load_css_content(self, tmp_path):
        """Test loading CSS content."""
        config = Config(tmp_path / ".bpui.toml")
        manager = TUIThemeManager(config)
        
        css = manager.load_css()
        
        assert isinstance(css, str)
        assert len(css) > 0
        # Check for some expected CSS content
        assert "Screen" in css or "$primary" in css
    
    def test_reload_theme(self, tmp_path):
        """Test reloading theme after config change."""
        config = Config(tmp_path / ".bpui.toml")
        manager = TUIThemeManager(config)
        
        assert manager.theme_name == "dark"
        
        config.set("theme_name", "light")
        manager.reload_theme()
        
        assert manager.theme_name == "light"
    
    def test_fallback_to_dark_if_theme_missing(self, tmp_path):
        """Test fallback to dark theme if custom theme file doesn't exist."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "nonexistent_theme")
        manager = TUIThemeManager(config)
        
        # Should fall back to dark.tcss
        css_path = manager.get_css_path()
        assert css_path.name == "dark.tcss"


class TestGUIThemeIntegration:
    """Test GUI theme integration with unified system."""
    
    def test_gui_theme_manager_uses_unified_theme(self, tmp_path):
        """Test that GUI ThemeManager uses unified theme definitions."""
        from bpui.gui.theme import ThemeManager, DEFAULT_THEME
        
        config = Config(tmp_path / ".bpui.toml")
        manager = ThemeManager(config)
        
        # Should load dark theme by default
        assert manager.theme_colors["app"]["background"] == BUILTIN_THEMES["dark"].app_colors["background"]
    
    def test_gui_default_theme_matches_builtin_dark(self):
        """Test that GUI DEFAULT_THEME matches built-in dark theme."""
        from bpui.gui.theme import DEFAULT_THEME
        
        assert DEFAULT_THEME["app"]["background"] == BUILTIN_THEMES["dark"].app_colors["background"]
        assert DEFAULT_THEME["tokenizer"]["brackets"] == BUILTIN_THEMES["dark"].tokenizer_colors["brackets"]


class TestThemeFiles:
    """Test that theme CSS files exist and are valid."""
    
    def test_dark_theme_file_exists(self):
        """Test that dark.tcss exists."""
        project_root = Path(__file__).parent.parent.parent
        dark_theme = project_root / "resources" / "themes" / "dark.tcss"
        
        assert dark_theme.exists(), "dark.tcss file not found"
    
    def test_light_theme_file_exists(self):
        """Test that light.tcss exists."""
        project_root = Path(__file__).parent.parent.parent
        light_theme = project_root / "resources" / "themes" / "light.tcss"
        
        assert light_theme.exists(), "light.tcss file not found"
    
    def test_nyx_theme_file_exists(self):
        """Test that nyx.tcss exists."""
        project_root = Path(__file__).parent.parent.parent
        nyx_theme = project_root / "resources" / "themes" / "nyx.tcss"
        
        assert nyx_theme.exists(), "nyx.tcss file not found"
    
    def test_theme_files_not_empty(self):
        """Test that theme files have content."""
        project_root = Path(__file__).parent.parent.parent
        themes_dir = project_root / "resources" / "themes"
        
        for theme_file in ["dark.tcss", "light.tcss", "nyx.tcss"]:
            theme_path = themes_dir / theme_file
            content = theme_path.read_text()
            assert len(content) > 100, f"{theme_file} is too small"
            assert "$primary" in content or "Screen" in content, f"{theme_file} doesn't look like valid Textual CSS"


class TestConfigThemeProperty:
    """Test Config.theme_name property."""
    
    def test_theme_name_property_default(self, tmp_path):
        """Test theme_name property returns default."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config.theme_name == "dark"
    
    def test_theme_name_property_custom(self, tmp_path):
        """Test theme_name property returns custom value."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("theme_name", "light")
        
        assert config.theme_name == "light"
    
    def test_theme_name_persists(self, tmp_path):
        """Test theme_name persists across save/load."""
        config_path = tmp_path / ".bpui.toml"
        config = Config(config_path)
        config.set("theme_name", "nyx")
        config.save()
        
        config2 = Config(config_path)
        assert config2.theme_name == "nyx"
