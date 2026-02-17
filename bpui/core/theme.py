"""Unified theme system for Blueprint UI (GUI + TUI).

This module defines the shared theme infrastructure used by both the Qt6 GUI
and the Textual TUI. Theme definitions live here; each frontend has its own
rendering logic (QSS for Qt, .tcss files for Textual).

Theme presets are stored as ThemeDefinition dataclasses. The active theme name
is persisted in .bpui.toml under the ``theme_name`` key. Custom themes can be
dropped as .tcss files into ``resources/themes/`` and they'll appear in the
theme picker automatically.
"""

from __future__ import annotations

import importlib.resources
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from bpui.utils.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Theme definition
# ---------------------------------------------------------------------------

@dataclass
class ThemeColors:
    """Color palette for a single theme."""

    # App-level colors (used by GUI QSS and mapped to TUI variables)
    background: str = "#1e1e1e"
    text: str = "#e0e0e0"
    accent: str = "#6200ea"
    button: str = "#3700b3"
    button_text: str = "#ffffff"
    border: str = "#424242"
    highlight: str = "#bb86fc"
    window: str = "#121212"

    # Tokenizer syntax-highlight colors (GUI review pane)
    tok_brackets: str = "#e91e63"
    tok_asterisk: str = "#2196f3"
    tok_parentheses: str = "#ff9800"
    tok_double_brackets: str = "#4caf50"
    tok_curly_braces: str = "#9c27b0"
    tok_pipes: str = "#00bcd4"
    tok_at_sign: str = "#ff5722"

    # Semantic GUI colors (used by property-based QSS selectors)
    muted_text: str = "#888888"
    surface: str = "#2a2a2a"
    success_bg: str = "#2d5f2d"
    danger_bg: str = "#5f2d2d"
    accent_bg: str = "#4a2d5f"
    accent_title: str = "#9b59b6"
    success_text: str = "#44aa44"
    error_text: str = "#ff4444"
    warning_text: str = "#ffaa44"

    # TUI-specific Textual design tokens
    tui_primary: str = "#6200ea"
    tui_secondary: str = "#03dac6"
    tui_surface: str = "#1e1e1e"
    tui_panel: str = "#2d2d2d"
    tui_warning: str = "#fb8c00"
    tui_error: str = "#cf6679"
    tui_success: str = "#4caf50"
    tui_accent: str = "#bb86fc"


@dataclass
class ThemeDefinition:
    """Complete theme definition."""

    name: str
    display_name: str
    description: str = ""
    is_builtin: bool = True
    colors: ThemeColors = field(default_factory=ThemeColors)

    # ---- Convenience accessors for legacy GUI format ----

    @property
    def app_colors(self) -> Dict[str, str]:
        """Return app color dict matching the legacy GUI DEFAULT_THEME['app'] format."""
        c = self.colors
        return {
            "background": c.background,
            "text": c.text,
            "accent": c.accent,
            "button": c.button,
            "button_text": c.button_text,
            "border": c.border,
            "highlight": c.highlight,
            "window": c.window,
            "muted_text": c.muted_text,
            "surface": c.surface,
            "success_bg": c.success_bg,
            "danger_bg": c.danger_bg,
            "accent_bg": c.accent_bg,
            "accent_title": c.accent_title,
            "success_text": c.success_text,
            "error_text": c.error_text,
            "warning_text": c.warning_text,
        }

    @property
    def tokenizer_colors(self) -> Dict[str, str]:
        """Return tokenizer color dict matching the legacy GUI DEFAULT_THEME['tokenizer'] format."""
        c = self.colors
        return {
            "brackets": c.tok_brackets,
            "asterisk": c.tok_asterisk,
            "parentheses": c.tok_parentheses,
            "double_brackets": c.tok_double_brackets,
            "curly_braces": c.tok_curly_braces,
            "pipes": c.tok_pipes,
            "at_sign": c.tok_at_sign,
        }

    @property
    def legacy_theme_dict(self) -> Dict[str, Dict[str, str]]:
        """Return the full legacy ``{"tokenizer": {...}, "app": {...}}`` dict."""
        return {
            "tokenizer": self.tokenizer_colors,
            "app": self.app_colors,
        }

    @property
    def tui_variables(self) -> Dict[str, str]:
        """Return Textual CSS variable mapping."""
        c = self.colors
        return {
            "primary": c.tui_primary,
            "secondary": c.tui_secondary,
            "surface": c.tui_surface,
            "panel": c.tui_panel,
            "warning": c.tui_warning,
            "error": c.tui_error,
            "success": c.tui_success,
            "accent": c.tui_accent,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (for config persistence)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Built-in theme presets
# ---------------------------------------------------------------------------

DARK_THEME = ThemeDefinition(
    name="dark",
    display_name="Dark",
    description="Default dark theme with purple accents",
    colors=ThemeColors(
        # App
        background="#1e1e1e",
        text="#e0e0e0",
        accent="#6200ea",
        button="#3700b3",
        button_text="#ffffff",
        border="#424242",
        highlight="#bb86fc",
        window="#121212",
        # Tokenizer
        tok_brackets="#e91e63",
        tok_asterisk="#2196f3",
        tok_parentheses="#ff9800",
        tok_double_brackets="#4caf50",
        tok_curly_braces="#9c27b0",
        tok_pipes="#00bcd4",
        tok_at_sign="#ff5722",
        # Semantic GUI
        muted_text="#888888",
        surface="#2a2a2a",
        success_bg="#2d5f2d",
        danger_bg="#5f2d2d",
        accent_bg="#4a2d5f",
        accent_title="#9b59b6",
        success_text="#44aa44",
        error_text="#ff4444",
        warning_text="#ffaa44",
        # TUI
        tui_primary="#6200ea",
        tui_secondary="#03dac6",
        tui_surface="#1e1e1e",
        tui_panel="#2d2d2d",
        tui_warning="#fb8c00",
        tui_error="#cf6679",
        tui_success="#4caf50",
        tui_accent="#bb86fc",
    ),
)

LIGHT_THEME = ThemeDefinition(
    name="light",
    display_name="Light",
    description="Clean light theme for bright environments",
    colors=ThemeColors(
        # App
        background="#fafafa",
        text="#212121",
        accent="#1565c0",
        button="#1976d2",
        button_text="#ffffff",
        border="#bdbdbd",
        highlight="#90caf9",
        window="#ffffff",
        # Tokenizer
        tok_brackets="#c62828",
        tok_asterisk="#1565c0",
        tok_parentheses="#e65100",
        tok_double_brackets="#2e7d32",
        tok_curly_braces="#6a1b9a",
        tok_pipes="#00838f",
        tok_at_sign="#d84315",
        # Semantic GUI
        muted_text="#757575",
        surface="#f0f0f0",
        success_bg="#2e7d32",
        danger_bg="#c62828",
        accent_bg="#1565c0",
        accent_title="#7b1fa2",
        success_text="#2e7d32",
        error_text="#c62828",
        warning_text="#ef6c00",
        # TUI
        tui_primary="#1565c0",
        tui_secondary="#00897b",
        tui_surface="#fafafa",
        tui_panel="#f5f5f5",
        tui_warning="#ef6c00",
        tui_error="#c62828",
        tui_success="#2e7d32",
        tui_accent="#42a5f5",
    ),
)

NYX_THEME = ThemeDefinition(
    name="nyx",
    display_name="Nyx",
    description="Deep purple and magenta — the blueprint architect's choice",
    colors=ThemeColors(
        # App
        background="#0d0221",
        text="#e8d5f5",
        accent="#e91e63",
        button="#880e4f",
        button_text="#fce4ec",
        border="#4a148c",
        highlight="#f48fb1",
        window="#1a0533",
        # Tokenizer
        tok_brackets="#ff4081",
        tok_asterisk="#7c4dff",
        tok_parentheses="#ffab40",
        tok_double_brackets="#69f0ae",
        tok_curly_braces="#ea80fc",
        tok_pipes="#18ffff",
        tok_at_sign="#ff6e40",
        # Semantic GUI
        muted_text="#9e8fb5",
        surface="#150330",
        success_bg="#1b5e20",
        danger_bg="#5f2d3d",
        accent_bg="#880e4f",
        accent_title="#f48fb1",
        success_text="#69f0ae",
        error_text="#ff5252",
        warning_text="#ffab40",
        # TUI
        tui_primary="#e91e63",
        tui_secondary="#7c4dff",
        tui_surface="#0d0221",
        tui_panel="#1a0533",
        tui_warning="#ffab40",
        tui_error="#ff5252",
        tui_success="#69f0ae",
        tui_accent="#f48fb1",
    ),
)

BUILTIN_THEMES: Dict[str, ThemeDefinition] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "nyx": NYX_THEME,
    "custom": DARK_THEME,  # Sentinel - uses dark as base with config overrides
}

DEFAULT_THEME_NAME = "dark"


# ---------------------------------------------------------------------------
# Theme resolution helpers
# ---------------------------------------------------------------------------

def _get_themes_dir() -> Path:
    """Return the ``resources/themes/`` directory path."""
    # Walk up from this file to the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    themes_dir = project_root / "resources" / "themes"
    return themes_dir


def list_available_themes() -> List[str]:
    """Return names of all available themes (built-in + custom .tcss files).

    Custom themes are discovered by scanning ``resources/themes/`` for ``.tcss``
    files whose stem doesn't match a built-in name.
    """
    names = list(BUILTIN_THEMES.keys())

    themes_dir = _get_themes_dir()
    if themes_dir.is_dir():
        for tcss_file in sorted(themes_dir.glob("*.tcss")):
            stem = tcss_file.stem
            if stem not in names:
                names.append(stem)

    return names


def get_theme(name: str) -> ThemeDefinition:
    """Get a theme by name.

    For built-in themes, returns the preset. For custom themes, returns a
    ThemeDefinition with default colors (the TUI uses the .tcss file directly).

    Raises:
        ValueError: If the theme name is not found.
    """
    if name in BUILTIN_THEMES:
        return BUILTIN_THEMES[name]

    # Check for custom .tcss file
    themes_dir = _get_themes_dir()
    tcss_path = themes_dir / f"{name}.tcss"
    if tcss_path.is_file():
        return ThemeDefinition(
            name=name,
            display_name=name.replace("_", " ").replace("-", " ").title(),
            description=f"Custom theme from {tcss_path.name}",
            is_builtin=False,
        )

    raise ValueError(
        f"Unknown theme '{name}'. Available: {', '.join(list_available_themes())}"
    )


def load_theme_from_config(config) -> ThemeDefinition:
    """Load the active theme from a Config instance.

    Reads ``config.get("theme_name")`` and resolves it. If the config also has
    a ``[theme]`` section with custom color overrides, those are applied on top
    of the base theme.

    Args:
        config: A ``bpui.core.config.Config`` instance.

    Returns:
        The resolved ThemeDefinition.
    """
    theme_name = config.get("theme_name", DEFAULT_THEME_NAME)

    # For "custom" theme, start with dark as base and apply overrides
    if theme_name == "custom":
        theme = BUILTIN_THEMES[DEFAULT_THEME_NAME]
        custom_overrides = config.get("theme", {})
        if custom_overrides and isinstance(custom_overrides, dict):
            theme = _apply_custom_overrides(theme, custom_overrides)
            # Mark as custom
            theme.name = "custom"
        return theme

    try:
        theme = get_theme(theme_name)
    except ValueError:
        logger.warning(f"Theme '{theme_name}' not found, falling back to '{DEFAULT_THEME_NAME}'")
        theme = BUILTIN_THEMES[DEFAULT_THEME_NAME]

    # Apply custom color overrides from [theme] config section
    custom_overrides = config.get("theme", {})
    if custom_overrides and isinstance(custom_overrides, dict):
        theme = _apply_custom_overrides(theme, custom_overrides)

    return theme


# Backwards compatibility alias
load_theme = load_theme_from_config


def save_theme_selection(config, theme_name: str) -> None:
    """Persist the active theme name to config.

    Args:
        config: A ``bpui.core.config.Config`` instance.
        theme_name: Name of the theme to activate.
    """
    config.set("theme_name", theme_name)
    config.save()
    logger.info(f"Theme set to '{theme_name}'")


def _apply_custom_overrides(
    base: ThemeDefinition, overrides: Dict[str, Any]
) -> ThemeDefinition:
    """Apply custom color overrides from config onto a base theme.

    The overrides dict uses the legacy GUI format::

        {
            "tokenizer": {"brackets": "#ff0000", ...},
            "app": {"background": "#000000", ...}
        }
    """
    import copy
    theme = copy.deepcopy(base)
    colors = theme.colors

    # Map legacy "app" keys to ThemeColors fields
    app_map = {
        "background": "background",
        "text": "text",
        "accent": "accent",
        "button": "button",
        "button_text": "button_text",
        "border": "border",
        "highlight": "highlight",
        "window": "window",
        "muted_text": "muted_text",
        "surface": "surface",
        "success_bg": "success_bg",
        "danger_bg": "danger_bg",
        "accent_bg": "accent_bg",
        "accent_title": "accent_title",
        "success_text": "success_text",
        "error_text": "error_text",
        "warning_text": "warning_text",
    }

    # Map legacy "tokenizer" keys to ThemeColors fields
    tok_map = {
        "brackets": "tok_brackets",
        "asterisk": "tok_asterisk",
        "parentheses": "tok_parentheses",
        "double_brackets": "tok_double_brackets",
        "curly_braces": "tok_curly_braces",
        "pipes": "tok_pipes",
        "at_sign": "tok_at_sign",
    }

    app_overrides = overrides.get("app", {})
    if isinstance(app_overrides, dict):
        for legacy_key, field_name in app_map.items():
            if legacy_key in app_overrides:
                setattr(colors, field_name, app_overrides[legacy_key])

    tok_overrides = overrides.get("tokenizer", {})
    if isinstance(tok_overrides, dict):
        for legacy_key, field_name in tok_map.items():
            if legacy_key in tok_overrides:
                setattr(colors, field_name, tok_overrides[legacy_key])

    return theme


# ---------------------------------------------------------------------------
# TUI theme CSS management
# ---------------------------------------------------------------------------

def get_tui_css_path(theme_name: str) -> Path:
    """Return the path to the .tcss file for a given theme.

    Args:
        theme_name: Name of the theme.

    Returns:
        Path to the .tcss file.

    Raises:
        FileNotFoundError: If the .tcss file doesn't exist.
    """
    themes_dir = _get_themes_dir()
    css_path = themes_dir / f"{theme_name}.tcss"

    if not css_path.is_file():
        raise FileNotFoundError(
            f"TUI theme CSS not found: {css_path}\n"
            f"Available themes: {', '.join(list_available_themes())}"
        )

    return css_path


def load_tui_css(theme_name: str) -> str:
    """Load and return the Textual CSS content for a theme.

    Args:
        theme_name: Name of the theme.

    Returns:
        The CSS string content.
    """
    css_path = get_tui_css_path(theme_name)
    return css_path.read_text(encoding="utf-8")
