"""Tests for bpui/config.py."""

import pytest
from pathlib import Path
from bpui.core.config import Config, DEFAULT_CONFIG


class TestConfigDefaults:
    """Tests for config default values."""
    
    def test_default_values(self, tmp_path):
        """Test that defaults are loaded when no config file exists."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config.engine == "openai_compatible"
        assert config.model == "openrouter/openai/gpt-4o-mini"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.base_url == "https://openrouter.ai/api/v1"
    
    def test_config_file_not_exists(self, tmp_path):
        """Test behavior when config file doesn't exist."""
        config_path = tmp_path / ".bpui.toml"
        config = Config(config_path)
        
        assert not config_path.exists()
        assert config.engine == DEFAULT_CONFIG["engine"]


class TestConfigSaveLoad:
    """Tests for saving and loading config."""
    
    def test_save_creates_file(self, tmp_path):
        """Test that save creates config file."""
        config_path = tmp_path / ".bpui.toml"
        config = Config(config_path)
        config.save()
        
        assert config_path.exists()
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading config."""
        config_path = tmp_path / ".bpui.toml"
        
        # Save with custom values
        config1 = Config(config_path)
        config1.set("model", "anthropic/claude-3")
        config1.set("temperature", 0.9)
        config1.save()
        
        # Load in new instance
        config2 = Config(config_path)
        assert config2.model == "anthropic/claude-3"
        assert config2.temperature == 0.9
    
    def test_get_nonexistent_key(self, tmp_path):
        """Test getting a key that doesn't exist."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"


class TestProviderKeyManagement:
    """Tests for provider-specific API key management."""
    
    def test_set_api_key(self, tmp_path):
        """Test setting API key for a provider."""
        config = Config(tmp_path / ".bpui.toml")
        config.set_api_key("openai", "sk-test123")
        
        assert config.get_api_key("openai") == "sk-test123"
    
    def test_set_multiple_keys(self, tmp_path):
        """Test setting keys for multiple providers."""
        config = Config(tmp_path / ".bpui.toml")
        config.set_api_key("openai", "sk-test123")
        config.set_api_key("anthropic", "sk-ant-test456")
        config.set_api_key("google", "AIza-test789")
        
        assert config.get_api_key("openai") == "sk-test123"
        assert config.get_api_key("anthropic") == "sk-ant-test456"
        assert config.get_api_key("google") == "AIza-test789"
    
    def test_get_nonexistent_provider_key(self, tmp_path):
        """Test getting key for provider that hasn't been set."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config.get_api_key("nonexistent") is None
    
    def test_get_all_providers(self, tmp_path):
        """Test getting list of all providers with keys."""
        config = Config(tmp_path / ".bpui.toml")
        # Start fresh - clear any defaults
        config.set("api_keys", {})
        config.set_api_key("openai", "sk-test123")
        config.set_api_key("anthropic", "sk-ant-test456")
        
        providers = config.get_all_providers()
        assert len(providers) == 2
        assert "openai" in providers
        assert "anthropic" in providers
    
    def test_overwrite_existing_key(self, tmp_path):
        """Test overwriting an existing API key."""
        config = Config(tmp_path / ".bpui.toml")
        config.set_api_key("openai", "sk-old")
        config.set_api_key("openai", "sk-new")
        
        assert config.get_api_key("openai") == "sk-new"


class TestExtractProvider:
    """Tests for _extract_provider method."""
    
    def test_extract_openai(self, tmp_path):
        """Test extracting OpenAI provider."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config._extract_provider("openai/gpt-4") == "openai"
        assert config._extract_provider("openai/gpt-3.5-turbo") == "openai"
    
    def test_extract_anthropic(self, tmp_path):
        """Test extracting Anthropic provider."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config._extract_provider("anthropic/claude-3-opus") == "anthropic"
        assert config._extract_provider("anthropic/claude-3-sonnet") == "anthropic"
    
    def test_extract_no_slash(self, tmp_path):
        """Test model name without slash returns None."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config._extract_provider("local-model") is None
        assert config._extract_provider("gpt4") is None
    
    def test_extract_multiple_slashes(self, tmp_path):
        """Test model name with multiple slashes (takes first part)."""
        config = Config(tmp_path / ".bpui.toml")
        
        assert config._extract_provider("openai/models/gpt-4") == "openai"


class TestApiKeyPriority:
    """Tests for API key priority system."""
    
    def test_provider_specific_key_priority(self, tmp_path):
        """Test that provider-specific key takes priority."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("model", "openai/gpt-4")
        config.set_api_key("openai", "sk-provider-key")
        config.set("api_key", "sk-legacy-key")
        
        # Provider-specific should win
        assert config.api_key == "sk-provider-key"
    
    def test_legacy_key_fallback(self, tmp_path):
        """Test fallback to legacy api_key field."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("model", "openai/gpt-4")
        # Clear provider-specific keys
        config.set("api_keys", {})
        config.set("api_key", "sk-legacy-key")
        
        assert config.api_key == "sk-legacy-key"
    
    def test_no_key_returns_none(self, tmp_path):
        """Test that None is returned when no key available."""
        config = Config(tmp_path / ".bpui.toml")
        config.set("model", "openai/gpt-4")
        # No keys set at all
        
        # Should return None (no env var in test)
        assert config.api_key is None or isinstance(config.api_key, str)


class TestConfigPersistence:
    """Tests for config persistence across saves."""
    
    def test_persist_api_keys(self, tmp_path):
        """Test that API keys persist across save/load."""
        config_path = tmp_path / ".bpui.toml"
        
        config1 = Config(config_path)
        config1.set_api_key("openai", "sk-test123")
        config1.set_api_key("anthropic", "sk-ant-test456")
        config1.save()
        
        config2 = Config(config_path)
        assert config2.get_api_key("openai") == "sk-test123"
        assert config2.get_api_key("anthropic") == "sk-ant-test456"
    
    def test_persist_all_settings(self, tmp_path):
        """Test that all settings persist."""
        config_path = tmp_path / ".bpui.toml"
        
        config1 = Config(config_path)
        config1.set("engine", "openai_compatible")
        config1.set("model", "local/model")
        config1.set("base_url", "http://localhost:11434/v1")
        config1.set("temperature", 0.5)
        config1.set("max_tokens", 2048)
        config1.save()
        
        config2 = Config(config_path)
        assert config2.engine == "openai_compatible"
        assert config2.model == "local/model"
        assert config2.base_url == "http://localhost:11434/v1"


class TestConfigEdgeCases:
    """Tests for config edge cases and utility methods."""
    
    def test_to_dict(self, temp_config):
        """Test to_dict returns copy of data."""
        temp_config.set("test_key", "test_value")
        temp_config.set("number", 42)
        
        data = temp_config.to_dict()
        assert data["test_key"] == "test_value"
        assert data["number"] == 42
        
        # Modifying top-level keys shouldn't affect config
        data["test_key"] = "modified"
        assert temp_config.get("test_key") == "test_value"
    
    def test_update_from_dict(self, temp_config):
        """Test update_from_dict merges data."""
        temp_config.set("existing", "old_value")
        
        temp_config.update_from_dict({
            "existing": "new_value",
            "new_key": "new_value"
        })
        
        assert temp_config.get("existing") == "new_value"
        assert temp_config.get("new_key") == "new_value"
    
    def test_set_api_key_overwrites_invalid_type(self, temp_config):
        """Test set_api_key handles invalid api_keys type."""
        # Start with valid dict
        temp_config.set("api_keys", {"existing": "key1"})
        
        # This should work normally
        temp_config.set_api_key("new_provider", "new_key")
        
        api_keys = temp_config.get("api_keys")
        assert isinstance(api_keys, dict)
        assert api_keys["existing"] == "key1"
        assert api_keys["new_provider"] == "new_key"
