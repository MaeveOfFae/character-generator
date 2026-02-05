"""Configuration management for Blueprint UI."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from .logging_config import setup_logging, get_logger


DEFAULT_CONFIG = {
    "engine": "litellm",
    "model": "openai/gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "api_key": "",  # Legacy single key (deprecated)
    "base_url": "",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_keys": {},  # Provider-specific keys: {"openai": "sk-...", "anthropic": "sk-ant-..."}
}


class Config:
    """Blueprint UI configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config from file or defaults."""
        self.config_path = config_path or Path.cwd() / ".bpui.toml"
        self._data: Dict[str, Any] = {}
        self._logger = get_logger(__name__)
        self._setup_logging_if_needed()
        self.load()
    
    def _setup_logging_if_needed(self) -> None:
        """Set up logging if not already configured."""
        root_logger = get_logger("bpui")
        if not root_logger.handlers:
            log_level = os.getenv("BPUI_LOG_LEVEL", "INFO")
            log_to_file = os.getenv("BPUI_LOG_FILE")
            
            log_file = Path(log_to_file) if log_to_file else None
            setup_logging(
                level=log_level,
                log_file=log_file,
                log_to_console=True,
            )
            self._logger.debug(f"Logging initialized at {log_level} level")

    def load(self) -> None:
        """Load config from file or use defaults."""
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                self._data = tomllib.load(f)
            self._logger.debug(f"Loaded config from {self.config_path}")
        else:
            self._data = DEFAULT_CONFIG.copy()
            self._logger.debug("Using default configuration")

    def save(self) -> None:
        """Save config to file."""
        with open(self.config_path, "wb") as f:
            tomli_w.dump(self._data, f)
        self._logger.info(f"Saved config to {self.config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        self._data[key] = value

    @property
    def engine(self) -> str:
        """Get engine type."""
        return self.get("engine", "litellm")

    @property
    def model(self) -> str:
        """Get model name."""
        return self.get("model", "openai/gpt-4")

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from config or environment.
        
        Priority:
        1. Provider-specific key from api_keys dict (based on model)
        2. Legacy direct api_key field
        3. Environment variable from api_key_env
        """
        # Extract provider from model (e.g., "openai/gpt-4" -> "openai")
        provider = self._extract_provider(self.model)
        
        # Check provider-specific keys first
        api_keys = self.get("api_keys", {})
        if provider and provider in api_keys and api_keys[provider]:
            return api_keys[provider]
        
        # Fall back to legacy direct key
        direct_key = self.get("api_key", "")
        if direct_key:
            return direct_key
        
        # Fall back to environment variable
        env_var = self.get("api_key_env", "")
        if env_var:
            return os.getenv(env_var)
        return None
    
    def _extract_provider(self, model: str) -> Optional[str]:
        """Extract provider name from model string.
        
        Examples:
            "openai/gpt-4" -> "openai"
            "anthropic/claude-3" -> "anthropic"
            "local-model" -> None
        """
        if "/" in model:
            return model.split("/")[0]
        return None
    
    def set_api_key(self, provider: str, key: str) -> None:
        """Set API key for a specific provider."""
        api_keys = self.get("api_keys", {})
        if not isinstance(api_keys, dict):
            api_keys = {}
        api_keys[provider] = key
        self.set("api_keys", api_keys)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        api_keys = self.get("api_keys", {})
        return api_keys.get(provider) if isinstance(api_keys, dict) else None
    
    def get_all_providers(self) -> list[str]:
        """Get list of all providers with stored keys."""
        api_keys = self.get("api_keys", {})
        if isinstance(api_keys, dict):
            return sorted([k for k, v in api_keys.items() if v])
        return []

    @property
    def base_url(self) -> str:
        """Get base URL for OpenAI-compatible engines."""
        return self.get("base_url", "")

    @property
    def temperature(self) -> float:
        """Get temperature."""
        return self.get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        """Get max tokens."""
        return self.get("max_tokens", 4096)

    def to_dict(self) -> Dict[str, Any]:
        """Get config as dict."""
        return self._data.copy()

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update config from dict."""
        self._data.update(data)
