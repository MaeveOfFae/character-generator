"""Unified theme system for Character Generator (GUI + TUI).

This module defines the shared theme infrastructure used by both the Qt6 GUI
and the Textual TUI. Theme definitions live here; each frontend has its own
rendering logic (QSS for Qt, .tcss files for Textual).

Theme presets are stored as ThemeDefinition dataclasses. The active theme name
is persisted in .bpui.toml under the ``theme_name`` key. Custom themes can be
dropped as .tcss files into ``resources/themes/`` and they'll appear in the
theme picker automatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import shutil
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

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
    author: str = ""
    tags: list[str] = field(default_factory=list)
    based_on: str = ""
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
# Theme loading
# ---------------------------------------------------------------------------


def _get_themes_dir() -> Path:
    """Return the ``resources/themes/`` directory path."""
    # Walk up from this file to the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    themes_dir = project_root / "resources" / "themes"
    return themes_dir


def _load_theme_from_file(path: Path) -> ThemeDefinition:
    """Load a theme from a .toml file."""
    with path.open("rb") as f:
        data = tomllib.load(f)
    colors_data = data.get("colors", {})
    # Filter colors_data to only include keys that are in ThemeColors
    valid_keys = {f.name for f in fields(ThemeColors)}
    filtered_colors = {k: v for k, v in colors_data.items() if k in valid_keys}
    colors = ThemeColors(**filtered_colors)
    return ThemeDefinition(
        name=data.get("name", path.stem),
        display_name=data.get("display_name", path.stem.replace("_", " ").title()),
        description=data.get("description", ""),
        author=data.get("author", ""),
        tags=[str(tag).strip() for tag in data.get("tags", []) if str(tag).strip()],
        based_on=data.get("based_on", ""),
        is_builtin=data.get("is_builtin", False),
        colors=colors,
    )


def _sanitize_theme_name(name: str) -> str:
    """Normalize a theme name for use as a filename and theme id."""
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().lower()).strip("_")
    if not normalized:
        raise ValueError("Theme name cannot be empty")
    return normalized


def _theme_toml_path(name: str) -> Path:
    return _get_themes_dir() / f"{name}.toml"


def _theme_tcss_path(name: str) -> Path:
    return _get_themes_dir() / f"{name}.tcss"


def theme_exists(name: str) -> bool:
    """Return whether a theme name already exists as built-in or custom."""
    sanitized_name = _sanitize_theme_name(name)
    return (
        sanitized_name in BUILTIN_THEMES
        or _theme_toml_path(sanitized_name).exists()
        or _theme_tcss_path(sanitized_name).exists()
    )


def _generate_unique_theme_name(base_name: str) -> str:
    """Generate a unique theme name based on the provided base name."""
    sanitized_base = _sanitize_theme_name(base_name)
    if not theme_exists(sanitized_base):
        return sanitized_base

    index = 2
    while theme_exists(f"{sanitized_base}_{index}"):
        index += 1
    return f"{sanitized_base}_{index}"


def _theme_to_toml_payload(theme: ThemeDefinition) -> Dict[str, Any]:
    return {
        "name": theme.name,
        "display_name": theme.display_name,
        "description": theme.description,
        "author": theme.author,
        "tags": theme.tags,
        "based_on": theme.based_on,
        "is_builtin": theme.is_builtin,
        "colors": asdict(theme.colors),
    }


def _normalize_theme_tags(tags: Optional[List[str]]) -> list[str]:
    if not tags:
        return []
    normalized_tags: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = str(tag).strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized_tags.append(cleaned)
    return normalized_tags


def _write_theme_files(theme: ThemeDefinition, source_style_name: Optional[str] = None) -> None:
    """Write TOML and TCSS files for a theme.

    The TCSS layout rules are copied from an existing source theme because the
    Textual styles are layout-oriented and consume design tokens rather than
    hard-coded palette values.
    """
    themes_dir = _get_themes_dir()
    themes_dir.mkdir(parents=True, exist_ok=True)

    toml_path = _theme_toml_path(theme.name)
    tcss_path = _theme_tcss_path(theme.name)

    with toml_path.open("wb") as file_obj:
        tomli_w.dump(_theme_to_toml_payload(theme), file_obj)

    source_name = source_style_name or (theme.name if _theme_tcss_path(theme.name).exists() else DEFAULT_THEME_NAME)
    source_tcss_path = _theme_tcss_path(source_name)
    if not source_tcss_path.exists():
        source_tcss_path = _theme_tcss_path(DEFAULT_THEME_NAME)
    if source_tcss_path.resolve() != tcss_path.resolve():
        shutil.copyfile(source_tcss_path, tcss_path)


def _ensure_custom_theme(name: str) -> None:
    if name == "custom":
        raise ValueError("The reserved 'custom' theme cannot be modified")
    if name in BUILTIN_THEMES and BUILTIN_THEMES[name].is_builtin:
        raise ValueError(f"Built-in theme '{name}' cannot be modified")


def _load_themes_from_disk() -> Dict[str, ThemeDefinition]:
    """Load all themes from the resources/themes directory."""
    themes_dir = _get_themes_dir()
    themes = {}
    if themes_dir.is_dir():
        for toml_file in sorted(themes_dir.glob("*.toml")):
            try:
                theme = _load_theme_from_file(toml_file)
                themes[theme.name] = theme
            except Exception as e:
                logger.warning(f"Failed to load theme {toml_file.name}: {e}")
    return themes


BUILTIN_THEMES: Dict[str, ThemeDefinition] = {}


def reload_themes():
    """Force-reload all themes from disk."""
    global BUILTIN_THEMES
    BUILTIN_THEMES = _load_themes_from_disk()
    # Add the sentinel for "custom" theme.
    if "dark" in BUILTIN_THEMES:
        # Use the dark theme as the base for custom themes
        BUILTIN_THEMES["custom"] = BUILTIN_THEMES["dark"]
    else:
        # Fallback if dark theme isn't loaded for some reason
        BUILTIN_THEMES["custom"] = ThemeDefinition(
            name="custom", display_name="Custom", colors=ThemeColors()
        )
    logger.info(f"Reloaded themes. Found: {', '.join(BUILTIN_THEMES.keys())}")


# Initial load at startup
reload_themes()


DEFAULT_THEME_NAME = "dark"


# ---------------------------------------------------------------------------
# Theme resolution helpers
# ---------------------------------------------------------------------------

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


def list_theme_presets(include_reserved: bool = False) -> List[ThemeDefinition]:
    """Return theme presets sorted with built-ins first, then custom themes."""
    names = list_available_themes()
    if not include_reserved:
        names = [name for name in names if name != "custom"]

    themes = [get_theme(name) for name in names]
    return sorted(themes, key=lambda theme: (not theme.is_builtin, theme.display_name.lower()))


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


def create_custom_theme(
    name: str,
    display_name: str,
    colors: Dict[str, Any],
    description: str = "",
    author: str = "",
    tags: Optional[List[str]] = None,
    based_on: str = "",
    source_style_name: Optional[str] = None,
) -> ThemeDefinition:
    """Create a new reusable custom theme preset."""
    sanitized_name = _sanitize_theme_name(name)
    if sanitized_name in BUILTIN_THEMES or _theme_toml_path(sanitized_name).exists():
        raise ValueError(f"Theme '{sanitized_name}' already exists")

    theme = ThemeDefinition(
        name=sanitized_name,
        display_name=display_name.strip() or sanitized_name.replace("_", " ").title(),
        description=description,
        author=author.strip(),
        tags=_normalize_theme_tags(tags),
        based_on=based_on.strip(),
        is_builtin=False,
        colors=ThemeColors(**colors),
    )
    _write_theme_files(theme, source_style_name=source_style_name)
    reload_themes()
    return get_theme(sanitized_name)


def update_custom_theme(
    name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    based_on: Optional[str] = None,
    colors: Optional[Dict[str, Any]] = None,
) -> ThemeDefinition:
    """Update an existing custom theme preset."""
    sanitized_name = _sanitize_theme_name(name)
    _ensure_custom_theme(sanitized_name)

    existing = get_theme(sanitized_name)
    updated = ThemeDefinition(
        name=existing.name,
        display_name=display_name if display_name is not None else existing.display_name,
        description=description if description is not None else existing.description,
        author=author.strip() if author is not None else existing.author,
        tags=_normalize_theme_tags(tags) if tags is not None else existing.tags,
        based_on=based_on.strip() if based_on is not None else existing.based_on,
        is_builtin=False,
        colors=ThemeColors(**(colors or asdict(existing.colors))),
    )
    _write_theme_files(updated, source_style_name=existing.name)
    reload_themes()
    return get_theme(sanitized_name)


def duplicate_theme(
    name: str,
    new_name: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    based_on: Optional[str] = None,
) -> ThemeDefinition:
    """Duplicate any theme into a new custom preset."""
    source_theme = get_theme(name)
    return create_custom_theme(
        name=new_name,
        display_name=display_name or f"{source_theme.display_name} Copy",
        description=description if description is not None else source_theme.description,
        author=author if author is not None else source_theme.author,
        tags=tags if tags is not None else source_theme.tags,
        based_on=based_on if based_on is not None else source_theme.based_on,
        colors=asdict(source_theme.colors),
        source_style_name=source_theme.name if _theme_tcss_path(source_theme.name).exists() else DEFAULT_THEME_NAME,
    )


def rename_custom_theme(name: str, new_name: str, display_name: Optional[str] = None) -> ThemeDefinition:
    """Rename a custom theme preset and its backing files."""
    old_name = _sanitize_theme_name(name)
    new_sanitized_name = _sanitize_theme_name(new_name)
    _ensure_custom_theme(old_name)

    if new_sanitized_name != old_name and (new_sanitized_name in BUILTIN_THEMES or _theme_toml_path(new_sanitized_name).exists()):
        raise ValueError(f"Theme '{new_sanitized_name}' already exists")

    existing = get_theme(old_name)
    theme = ThemeDefinition(
        name=new_sanitized_name,
        display_name=display_name or existing.display_name,
        description=existing.description,
        author=existing.author,
        tags=existing.tags,
        based_on=existing.based_on,
        is_builtin=False,
        colors=existing.colors,
    )

    old_toml_path = _theme_toml_path(old_name)
    old_tcss_path = _theme_tcss_path(old_name)
    if old_toml_path.exists() and old_name != new_sanitized_name:
        old_toml_path.unlink()
    if old_tcss_path.exists() and old_name != new_sanitized_name:
        old_tcss_path.unlink()

    _write_theme_files(theme, source_style_name=old_name)
    reload_themes()
    return get_theme(new_sanitized_name)


def delete_custom_theme(name: str) -> None:
    """Delete a custom theme preset from disk."""
    sanitized_name = _sanitize_theme_name(name)
    _ensure_custom_theme(sanitized_name)

    toml_path = _theme_toml_path(sanitized_name)
    tcss_path = _theme_tcss_path(sanitized_name)
    if toml_path.exists():
        toml_path.unlink()
    if tcss_path.exists():
        tcss_path.unlink()
    reload_themes()


def import_theme_definition(
    name: str,
    display_name: str,
    colors: Dict[str, Any],
    description: str = "",
    author: str = "",
    tags: Optional[List[str]] = None,
    based_on: str = "",
    conflict_strategy: str = "reject",
    target_name: Optional[str] = None,
) -> ThemeDefinition:
    """Import a theme preset with explicit conflict handling."""
    imported_name = _sanitize_theme_name(name)
    desired_name = _sanitize_theme_name(target_name) if target_name else imported_name

    if conflict_strategy not in {"reject", "rename", "overwrite"}:
        raise ValueError(f"Unsupported conflict strategy '{conflict_strategy}'")

    if theme_exists(desired_name):
        if conflict_strategy == "reject":
            raise ValueError(f"Theme '{desired_name}' already exists")

        if conflict_strategy == "overwrite":
            _ensure_custom_theme(desired_name)
            return update_custom_theme(
                name=desired_name,
                display_name=display_name,
                description=description,
                author=author,
                tags=tags,
                based_on=based_on,
                colors=colors,
            )

        if target_name:
            raise ValueError(f"Theme '{desired_name}' already exists")

        desired_name = _generate_unique_theme_name(imported_name)

    return create_custom_theme(
        name=desired_name,
        display_name=display_name,
        description=description,
        author=author,
        tags=tags,
        based_on=based_on,
        colors=colors,
    )


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

    tui_map = {
        "primary": "tui_primary",
        "secondary": "tui_secondary",
        "surface": "tui_surface",
        "panel": "tui_panel",
        "warning": "tui_warning",
        "error": "tui_error",
        "success": "tui_success",
        "accent": "tui_accent",
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

    tui_overrides = overrides.get("tui", {})
    if isinstance(tui_overrides, dict):
        for legacy_key, field_name in tui_map.items():
            if legacy_key in tui_overrides:
                setattr(colors, field_name, tui_overrides[legacy_key])

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
