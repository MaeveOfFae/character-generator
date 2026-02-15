"""Test OpenRouter support through OpenAI-compatible API engine."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from bpui.llm.factory import detect_provider_from_model, create_engine
from bpui.llm.openai_compat_engine import OpenAICompatEngine


class TestOpenRouterDetection:
    """Test OpenRouter model detection."""

    def test_openrouter_claude_models(self):
        """Test OpenRouter Claude model detection."""
        models = [
            "openrouter/anthropic/claude-3-opus",
            "openrouter/anthropic/claude-3-sonnet",
            "openrouter/anthropic/claude-3-haiku",
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/anthropic/claude-instant-v1",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"

    def test_openrouter_openai_models(self):
        """Test OpenRouter OpenAI model detection."""
        models = [
            "openrouter/openai/gpt-3.5-turbo",
            "openrouter/openai/gpt-4",
            "openrouter/openai/gpt-4-turbo",
            "openrouter/openai/gpt-4o",
            "openrouter/openai/o1-preview",
            "openrouter/openai/o1-mini",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"

    def test_openrouter_google_models(self):
        """Test OpenRouter Google model detection."""
        models = [
            "openrouter/google/gemini-pro",
            "openrouter/google/gemini-pro-vision",
            "openrouter/google/palm-2-chat-bison",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"

    def test_openrouter_mistral_models(self):
        """Test OpenRouter Mistral model detection."""
        models = [
            "openrouter/mistralai/mistral-7b-instruct",
            "openrouter/mistralai/mistral-large",
            "openrouter/mistralai/mixtral-8x22b-instruct",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"

    def test_openrouter_meta_models(self):
        """Test OpenRouter Meta model detection."""
        models = [
            "openrouter/meta-llama/llama-2-13b-chat",
            "openrouter/meta-llama/llama-2-70b-chat",
            "openrouter/meta-llama/llama-3-70b-instruct",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"

    def test_openrouter_deepseek_models(self):
        """Test OpenRouter DeepSeek model detection."""
        models = [
            "openrouter/deepseek/deepseek-chat",
            "openrouter/deepseek/deepseek-coder",
        ]
        for model in models:
            assert detect_provider_from_model(model) == "openrouter", \
                f"Failed for {model}"


class TestOpenRouterEngineCreation:
    """Test OpenRouter engine creation."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock()
        config.model = "openrouter/anthropic/claude-3-opus"
        config.temperature = 0.7
        config.max_tokens = 4096
        config.get = Mock(side_effect=lambda key, default=None: {
            "engine_mode": "auto",
            "temperature": 0.7,
            "max_tokens": 4096,
        }.get(key, default))
        config.get_api_key = Mock(return_value="test-api-key")
        return config

    def test_openrouter_creates_openai_compat_engine(self, mock_config):
        """Test that OpenRouter models create OpenAICompatEngine."""
        engine = create_engine(mock_config)
        
        assert isinstance(engine, OpenAICompatEngine), \
            "OpenRouter models should create OpenAICompatEngine"
        assert engine.model == "openrouter/anthropic/claude-3-opus"
        assert engine.base_url == "https://openrouter.ai/api/v1"

    def test_openrouter_with_api_key_override(self, mock_config):
        """Test OpenRouter with API key override."""
        engine = create_engine(
            mock_config,
            api_key_override="override-key"
        )
        
        assert engine.api_key == "override-key"

    def test_openrouter_with_model_override(self, mock_config):
        """Test OpenRouter with model override."""
        engine = create_engine(
            mock_config,
            model_override="openrouter/openai/gpt-4"
        )
        
        assert engine.model == "openrouter/openai/gpt-4"

    def test_openrouter_with_temperature_override(self, mock_config):
        """Test OpenRouter with temperature override."""
        engine = create_engine(
            mock_config,
            temperature=0.9
        )
        
        assert engine.temperature == 0.9

    def test_openrouter_with_max_tokens_override(self, mock_config):
        """Test OpenRouter with max_tokens override."""
        engine = create_engine(
            mock_config,
            max_tokens=8192
        )
        
        assert engine.max_tokens == 8192


class TestOpenRouterApiKeys:
    """Test OpenRouter API key handling."""

    @pytest.fixture
    def mock_config_with_keys(self):
        """Create a mock config with provider-specific keys."""
        config = Mock()
        config.model = "openrouter/anthropic/claude-3-opus"
        config.temperature = 0.7
        config.max_tokens = 4096
        config.get = Mock(side_effect=lambda key, default=None: {
            "engine_mode": "auto",
            "temperature": 0.7,
            "max_tokens": 4096,
            "api_keys": {
                "openrouter": "or-test-key-123",
                "openai": "sk-test-key",
                "anthropic": "sk-ant-test-key",
            },
        }.get(key, default))
        
        def mock_get_api_key(provider):
            """Mock get_api_key to return provider-specific key."""
            api_keys = config.get("api_keys", {})
            return api_keys.get(provider)
        
        config.get_api_key = Mock(side_effect=mock_get_api_key)
        return config

    def test_openrouter_uses_provider_specific_key(self, mock_config_with_keys):
        """Test that OpenRouter uses provider-specific API key."""
        engine = create_engine(mock_config_with_keys)
        
        assert engine.api_key == "or-test-key-123"

    def test_openrouter_fallback_to_openai_key(self):
        """Test OpenRouter falls back to openai key if openrouter key not set."""
        config = Mock()
        config.model = "openrouter/openai/gpt-4"
        config.temperature = 0.7
        config.max_tokens = 4096
        config.get = Mock(side_effect=lambda key, default=None: {
            "engine_mode": "auto",
            "temperature": 0.7,
            "max_tokens": 4096,
            "api_keys": {
                "openai": "sk-test-key",
            },
        }.get(key, default))
        
        def mock_get_api_key(provider):
            """Mock get_api_key to return provider key."""
            api_keys = config.get("api_keys", {})
            # Try openrouter first, then fall back to openai
            key = api_keys.get(provider)
            if not key and provider == "openrouter":
                key = api_keys.get("openai")
            return key
        
        config.get_api_key = Mock(side_effect=mock_get_api_key)
        
        engine = create_engine(config)
        assert engine.api_key == "sk-test-key"


class TestOpenRouterModelsList:
    """Test various OpenRouter model formats."""

    @pytest.mark.parametrize("model", [
        # Anthropic
        "openrouter/anthropic/claude-2",
        "openrouter/anthropic/claude-3-opus",
        "openrouter/anthropic/claude-3-sonnet",
        "openrouter/anthropic/claude-3-haiku",
        "openrouter/anthropic/claude-3.5-sonnet",
        "openrouter/anthropic/claude-instant-v1",
        
        # OpenAI
        "openrouter/openai/gpt-3.5-turbo",
        "openrouter/openai/gpt-4",
        "openrouter/openai/gpt-4-turbo",
        "openrouter/openai/gpt-4o",
        "openrouter/openai/gpt-4-vision-preview",
        "openrouter/openai/o1-preview",
        "openrouter/openai/o1-mini",
        
        # Google
        "openrouter/google/gemini-pro",
        "openrouter/google/gemini-pro-vision",
        "openrouter/google/palm-2-chat-bison",
        "openrouter/google/palm-2-codechat-bison",
        
        # Meta
        "openrouter/meta-llama/llama-2-13b-chat",
        "openrouter/meta-llama/llama-2-70b-chat",
        "openrouter/meta-llama/llama-3-70b-instruct",
        "openrouter/meta-llama/codellama-34b-instruct",
        
        # Mistral
        "openrouter/mistralai/mistral-7b-instruct",
        "openrouter/mistralai/mistral-large",
        "openrouter/mistralai/mixtral-8x22b-instruct",
        
        # DeepSeek
        "openrouter/deepseek/deepseek-chat",
        "openrouter/deepseek/deepseek-coder",
        
        # Other providers
        "openrouter/cohere/command-r-plus",
        "openrouter/databricks/dbrx-instruct",
        "openrouter/qwen/qwen-2.5-coder-32b-instruct",
    ])
    def test_openrouter_model_detection(self, model):
        """Test that various OpenRouter models are detected correctly."""
        provider = detect_provider_from_model(model)
        assert provider == "openrouter", \
            f"Model '{model}' should be detected as openrouter provider"
