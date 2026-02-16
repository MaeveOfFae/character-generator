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
    "engine_mode": "auto",  # "auto" (detect from model) or "explicit" (use engine field)
    "model": "openai/gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "api_key": "",  # Legacy single key (deprecated)
    "base_url": "",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_keys": {},  # Provider-specific keys: {"openai": "sk-...", "anthropic": "sk-ant-..."}
    "batch": {
        "max_concurrent": 3,  # Max parallel batch operations
        "rate_limit_delay": 1.0,  # Seconds between batch starts
    },
    # Provider-specific configurations (optional)
    "google": {},  # e.g., {"top_k": 40, "top_p": 0.95, "safety_settings": [...]}
    "openai": {},  # e.g., {"seed": 42, "response_format": "json_object"}
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
            try:
                with open(self.config_path, "rb") as f:
                    self._data = tomllib.load(f)
                self._logger.debug(f"Loaded config from {self.config_path}")
                
                # Migrate deprecated engine values
                needs_save = False
                if self._data.get("engine") == "litellm":
                    self._logger.info("Migrating engine from 'litellm' to 'openai_compatible'")
                    self._data["engine"] = "openai_compatible"
                    needs_save = True
                
                # Ensure batch config exists (for compatibility with older config files)
                if "batch" not in self._data or not isinstance(self._data.get("batch"), dict):
                    self._logger.info("Adding missing batch configuration")
                    self._data["batch"] = DEFAULT_CONFIG["batch"].copy()
                    needs_save = True
                
                # Save if any migrations were performed
                if needs_save:
                    self.save()
                
                # Validate loaded config
                self._validate_config()
            except tomllib.TOMLDecodeError as e:
                self._logger.error(f"Invalid TOML in {self.config_path}: {e}")
                raise RuntimeError(
                    f"Config file is corrupted: {e}\n"
                    f"Location: {self.config_path}\n"
                    f"Please fix or delete the file to reset to defaults."
                ) from e
            except Exception as e:
                self._logger.error(f"Error loading config from {self.config_path}: {e}")
                raise RuntimeError(
                    f"Error loading config: {e}\n"
                    f"Location: {self.config_path}"
                ) from e
        else:
            self._data = DEFAULT_CONFIG.copy()
            self._logger.debug("Using default configuration")
    
    def _validate_config(self) -> None:
        """Validate loaded config values.
        
        Raises:
            ValueError: If required keys are missing or invalid
        """
        required_keys = ["engine", "model", "temperature", "max_tokens"]
        for key in required_keys:
            if key not in self._data:
                raise ValueError(f"Missing required config key: {key}")
        
        # Validate types
        if not isinstance(self._data["temperature"], (int, float)):
            raise ValueError("Config 'temperature' must be a number")
        if not isinstance(self._data["max_tokens"], int):
            raise ValueError("Config 'max_tokens' must be an integer")
        if not isinstance(self._data["engine"], str):
            raise ValueError("Config 'engine' must be a string")
        if not isinstance(self._data["model"], str):
            raise ValueError("Config 'model' must be a string")
        
        # Validate api_keys structure
        if "api_keys" in self._data:
            if not isinstance(self._data["api_keys"], dict):
                raise ValueError("Config 'api_keys' must be a dictionary")
            # Validate keys and values are strings
            for key, value in self._data["api_keys"].items():
                if not isinstance(key, str):
                    raise ValueError(f"api_keys key must be string, got {type(key)}")
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"api_keys value for '{key}' must be string or None")
        
        # Validate temperature range
        temp = self._data["temperature"]
        if temp < 0 or temp > 2:
            self._logger.warning(f"Temperature {temp} is outside typical range [0, 2]")
        
        # Validate max_tokens
        tokens = self._data["max_tokens"]
        if tokens <= 0:
            raise ValueError("Config 'max_tokens' must be positive")
        if tokens > 128000:
            self._logger.warning(f"max_tokens {tokens} is very large, may cause errors")

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
    
    def get_api_key_for_model(self, model: str) -> Optional[str]:
        """Get API key for a specific model.
        
        Extracts provider from model string and returns the appropriate key.
        Falls back to legacy config and environment variables.
        
        Examples:
            "openai/gpt-4" -> returns openai key
            "anthropic/claude-3" -> returns anthropic key
        """
        # Extract provider from model
        provider = self._extract_provider(model)
        
        # Check provider-specific keys first
        if provider:
            key = self.get_api_key(provider)
            if key:
                return key
        
        # Fall back to legacy direct key
        direct_key = self.get("api_key", "")
        if direct_key:
            return direct_key
        
        # Fall back to environment variable
        env_var = self.get("api_key_env", "")
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    def validate_api_key(self, model: str) -> None:
        """Validate that API key exists for model.
        
        Args:
            model: Model name to validate API key for
            
        Raises:
            ValueError: If no API key is configured for the model
        """
        key = self.get_api_key_for_model(model)
        if not key:
            provider = self._extract_provider(model) or "unknown provider"
            env_var = self.get("api_key_env", "OPENAI_API_KEY")
            raise ValueError(
                f"No API key configured for model '{model}' (provider: {provider}).\n"
                f"Set provider-specific key in config:\n"
                f"  bpui config set api_keys.{provider} YOUR_API_KEY\n"
                f"Or set environment variable: {env_var}"
            )
    
    def get_all_providers(self) -> list[str]:
        """Get list of all providers with stored keys."""
        api_keys = self.get("api_keys", {})
        if isinstance(api_keys, dict):
            return sorted([k for k, v in api_keys.items() if v])
        return []

    def get_engine_mode(self) -> str:
        """Get engine mode (auto or explicit).

        Returns:
            "auto" or "explicit"
        """
        return self.get("engine_mode", "auto")

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider-specific configuration.

        Args:
            provider: Provider name (e.g., "google", "openai")

        Returns:
            Dict of provider-specific config, or empty dict if not found
        """
        provider_config = self.get(provider, {})
        if isinstance(provider_config, dict):
            return provider_config.copy()
        return {}

    @property
    def base_url(self) -> str:
        """Get base URL for OpenAI-compatible engines."""
        return self.get("base_url", "")
    
    @property
    def api_base_url(self) -> str:
        """Get base URL for OpenAI-compatible engines (alias for base_url)."""
        return self.base_url
    
    @property
    def api_version(self) -> Optional[str]:
        """Get API version for OpenAI-compatible engines."""
        return self.get("api_version", None)

    @property
    def temperature(self) -> float:
        """Get temperature."""
        return self.get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        """Get max tokens."""
        return self.get("max_tokens", 4096)
    
    @property
    def batch_max_concurrent(self) -> int:
        """Get max concurrent batch operations."""
        batch_config = self.get("batch", {})
        return batch_config.get("max_concurrent", 3) if isinstance(batch_config, dict) else 3
    
    @property
    def batch_rate_limit_delay(self) -> float:
        """Get batch rate limit delay in seconds."""
        batch_config = self.get("batch", {})
        return batch_config.get("rate_limit_delay", 1.0) if isinstance(batch_config, dict) else 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Get config as dict."""
        return self._data.copy()

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update config from dict."""
        self._data.update(data)
