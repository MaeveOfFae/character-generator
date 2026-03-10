"""Configuration schemas."""

from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


EngineType = Literal["openai", "google", "openai_compatible", "auto"]
EngineMode = Literal["auto", "explicit"]
ContentMode = Literal["SFW", "NSFW", "Platform-Safe", "Auto"]


class BatchConfig(BaseModel):
    """Batch processing configuration."""
    max_concurrent: int = Field(default=3, ge=1, le=10)
    rate_limit_delay: float = Field(default=1.0, ge=0, le=60)


class ThemeAppColors(BaseModel):
    """Theme overrides for app-facing colors."""

    background: Optional[str] = None
    text: Optional[str] = None
    accent: Optional[str] = None
    button: Optional[str] = None
    button_text: Optional[str] = None
    border: Optional[str] = None
    highlight: Optional[str] = None
    window: Optional[str] = None
    muted_text: Optional[str] = None
    surface: Optional[str] = None
    success_bg: Optional[str] = None
    danger_bg: Optional[str] = None
    accent_bg: Optional[str] = None
    accent_title: Optional[str] = None
    success_text: Optional[str] = None
    error_text: Optional[str] = None
    warning_text: Optional[str] = None


class ThemeTokenizerColors(BaseModel):
    """Theme overrides for tokenizer colors."""

    brackets: Optional[str] = None
    asterisk: Optional[str] = None
    parentheses: Optional[str] = None
    double_brackets: Optional[str] = None
    curly_braces: Optional[str] = None
    pipes: Optional[str] = None
    at_sign: Optional[str] = None


class ThemeTuiColors(BaseModel):
    """Theme overrides for TUI design tokens."""

    primary: Optional[str] = None
    secondary: Optional[str] = None
    surface: Optional[str] = None
    panel: Optional[str] = None
    warning: Optional[str] = None
    error: Optional[str] = None
    success: Optional[str] = None
    accent: Optional[str] = None


class ThemeOverride(BaseModel):
    """Persisted custom theme override payload."""

    app: ThemeAppColors = Field(default_factory=ThemeAppColors)
    tokenizer: ThemeTokenizerColors = Field(default_factory=ThemeTokenizerColors)
    tui: ThemeTuiColors = Field(default_factory=ThemeTuiColors)


class ThemeColorsResponse(BaseModel):
    """Resolved theme palette."""

    background: str
    text: str
    accent: str
    button: str
    button_text: str
    border: str
    highlight: str
    window: str
    tok_brackets: str
    tok_asterisk: str
    tok_parentheses: str
    tok_double_brackets: str
    tok_curly_braces: str
    tok_pipes: str
    tok_at_sign: str
    muted_text: str
    surface: str
    success_bg: str
    danger_bg: str
    accent_bg: str
    accent_title: str
    success_text: str
    error_text: str
    warning_text: str
    tui_primary: str
    tui_secondary: str
    tui_surface: str
    tui_panel: str
    tui_warning: str
    tui_error: str
    tui_success: str
    tui_accent: str


class ThemePresetCreate(BaseModel):
    """Create a custom theme preset."""

    name: str
    display_name: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    based_on: str = ""
    colors: ThemeColorsResponse


class ThemePresetUpdate(BaseModel):
    """Update an existing custom theme preset."""

    display_name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[list[str]] = None
    based_on: Optional[str] = None
    colors: Optional[ThemeColorsResponse] = None


class ThemeDuplicateRequest(BaseModel):
    """Duplicate a theme preset under a new name."""

    new_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None


class ThemeRenameRequest(BaseModel):
    """Rename a custom theme preset."""

    new_name: str
    display_name: Optional[str] = None


class ThemePresetResponse(BaseModel):
    """Theme preset metadata and palette."""

    name: str
    display_name: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    based_on: str = ""
    is_builtin: bool = True
    colors: ThemeColorsResponse


class ConfigResponse(BaseModel):
    """Full configuration response."""
    engine: EngineType = "auto"
    engine_mode: EngineMode = "auto"
    model: str = "openrouter/openai/gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    api_keys: Dict[str, str] = Field(default_factory=dict)
    batch: BatchConfig = Field(default_factory=BatchConfig)
    base_url: Optional[str] = None
    theme_name: str = "dark"
    theme: ThemeOverride = Field(default_factory=ThemeOverride)
    available_providers: list[str] = Field(default_factory=lambda: ["openai", "google", "openrouter"])


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    engine: Optional[EngineType] = None
    engine_mode: Optional[EngineMode] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    api_keys: Optional[Dict[str, str]] = None
    batch: Optional[BatchConfig] = None
    base_url: Optional[str] = None
    theme_name: Optional[str] = None
    theme: Optional[ThemeOverride] = None


class ConnectionTestRequest(BaseModel):
    """Request to test an API connection."""
    provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    model_info: Optional[Dict[str, Any]] = None
