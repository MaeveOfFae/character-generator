"""Engine factory for creating LLM engines based on model and configuration."""

import logging
from typing import Optional, TYPE_CHECKING

from .base import LLMEngine

if TYPE_CHECKING:
    from bpui.core.config import Config

logger = logging.getLogger(__name__)


def _normalize_openai_compat_model(model: str, base_url: str) -> str:
    """Normalize model names for OpenAI-compatible APIs.

    OpenRouter expects provider/model IDs (e.g., "deepseek/deepseek-v3.2")
    and does not accept the legacy "openrouter/" prefix.
    """
    if "openrouter.ai" in (base_url or "").lower() and model.startswith("openrouter/"):
        return model[len("openrouter/"):]
    return model


def detect_provider_from_model(model: str) -> str:
    """Detect provider from model name.

    Args:
        model: Model name (e.g., "gpt-4", "gemini-1.5-pro", "openrouter/anthropic/claude-3-opus")

    Returns:
        Provider name: "google", "openai", "openrouter", or "unknown"

    Examples:
        "gpt-4" -> "openai"
        "gpt-4-turbo" -> "openai"
        "o1-preview" -> "openai"
        "gemini-1.5-pro" -> "google"
        "gemini-pro" -> "google"
        "openrouter/anthropic/claude-3-opus" -> "openrouter" (OpenAI-compatible API)
        "anthropic/claude-3-opus-20240229" -> "openrouter" (via autodetection)
        "deepseek/deepseek-chat" -> "deepseek"
        "zai/glm-5" -> "zai"
        "moonshot-v1-8k" -> "moonshot"
        "random-model" -> "unknown"
    """
    model_lower = model.lower()

    # Check for providers that use OpenAI-compatible APIs (like OpenRouter)
    # These are often specified with a prefix.
    if model_lower.startswith((
        "openrouter/",
        "openai/",
        "google/",
        "anthropic/",
        "deepseek/",
        "zai/",
        "moonshot",  # Moonshot models don't have a slash
    )):
        # Further check to map to a specific provider if needed,
        # but for now, we can treat them as compatible and route them
        # through a generic engine or a specific one if implemented.
        if model_lower.startswith("openrouter/"):
            return "openrouter"
        if model_lower.startswith("openai/"):
            return "openai"
        if model_lower.startswith("google/"):
            return "google"
        if model_lower.startswith("anthropic/"):
            return "anthropic"
        if model_lower.startswith("deepseek/"):
            return "deepseek"
        if model_lower.startswith("zai/"):
            return "zai"
        if model_lower.startswith("moonshot"):
            return "moonshot"

    # Auto-detect based on model name prefix for native APIs
    if model_lower.startswith(("gpt-", "o1-", "o1")):
        return "openai"

    if model_lower.startswith("gemini"):
        return "google"

    # Fallback for unknown models
    return "unknown"


def create_engine(
    config: "Config",
    model_override: Optional[str] = None,
    api_key_override: Optional[str] = None,
    **kwargs
) -> LLMEngine:
    """Create appropriate LLM engine based on config and model.

    This is the main entry point for creating engines. It handles:
    - Auto-detection of provider from model name
    - Explicit engine selection via config
    - API key resolution

    Args:
        config: Configuration object
        model_override: Optional model name to use instead of config.model
        api_key_override: Optional API key to use instead of config resolution
        **kwargs: Additional arguments to pass to engine constructor
                 (temperature, max_tokens, etc.)

    Returns:
        Instantiated LLMEngine subclass

    Raises:
        ValueError: If engine cannot be created or required dependencies missing
        ImportError: If native SDK required but not installed
    """
    from .openai_compat_engine import OpenAICompatEngine

    # Determine model to use
    model = model_override or config.model

    # Determine engine mode
    engine_mode = config.get("engine_mode", "auto")

    # Get common parameters from config and kwargs
    temperature = kwargs.pop("temperature", config.temperature)
    max_tokens = kwargs.pop("max_tokens", config.max_tokens)

    # Explicit mode: honor config.engine field
    if engine_mode == "explicit":
        engine_type = config.engine
        logger.info(f"Using explicit engine mode: {engine_type}")

        if engine_type == "openai_compatible":
            # Determine API key based on base_url
            if api_key_override:
                api_key = api_key_override
            elif "openrouter.ai" in (config.base_url or ""):
                # Use OpenRouter-specific API key for OpenRouter
                api_key = config.get_api_key("openrouter")
            else:
                # Fallback to generic api_key for other OpenAI-compatible APIs
                api_key = config.api_key

            base_url = config.base_url
            if not base_url:
                raise ValueError("OpenAI-compatible engine requires base_url in config")
            api_model = _normalize_openai_compat_model(model, base_url)
            return OpenAICompatEngine(
                model=api_model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url,
                **kwargs
            )
        elif engine_type == "google":
            return _create_google_engine(config, model, api_key_override, temperature, max_tokens, **kwargs)
        elif engine_type == "openai":
            return _create_openai_engine(config, model, api_key_override, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")

    # Auto mode: detect provider from model name
    provider = detect_provider_from_model(model)
    logger.info(f"Auto-detected provider '{provider}' from model '{model}'")

    if provider == "google":
        return _create_google_engine(config, model, api_key_override, temperature, max_tokens, **kwargs)
    elif provider == "openai":
        return _create_openai_engine(config, model, api_key_override, temperature, max_tokens, **kwargs)
    elif provider in ("openrouter", "anthropic", "deepseek", "zai", "moonshot"):
        # These providers can use either their direct API or OpenRouter
        # Try provider-specific key first for direct API, then fall back to OpenRouter
        provider_key = api_key_override or config.get_api_key(provider)
        openrouter_key = config.get_api_key("openrouter")
        
        # Determine which API to use based on available keys
        if provider == "openrouter" or (provider_key is None and openrouter_key):
            # Use OpenRouter (either explicitly or as fallback)
            api_key = api_key_override or openrouter_key
            base_url = "https://openrouter.ai/api/v1"
            # For OpenRouter, strip only the 'openrouter/' prefix if present
            # Model format expected by OpenRouter: 'provider/model' (e.g., 'anthropic/claude-3-opus')
            if model.startswith("openrouter/"):
                api_model = model[len("openrouter/"):]  # Strip 'openrouter/' prefix
            else:
                api_model = model  # Use as-is
            logger.info(f"Using OpenAICompatEngine for {provider} model '{model}' via OpenRouter (API: '{api_model}')")
        elif provider == "deepseek" and provider_key:
            # Use DeepSeek direct API
            api_key = provider_key
            base_url = "https://api.deepseek.com"
            api_model = model.split('/')[-1] if '/' in model else model
            logger.info(f"Using OpenAICompatEngine for DeepSeek direct API model '{model}' (API: '{api_model}')")
        elif provider == "anthropic" and provider_key:
            # Anthropic requires their own SDK, not OpenAI-compatible
            # For now, route through OpenRouter if we have that key
            if openrouter_key:
                api_key = openrouter_key
                base_url = "https://openrouter.ai/api/v1"
                # For OpenRouter, need provider/model format
                if model.startswith("openrouter/"):
                    api_model = model[len("openrouter/"):]
                elif model.startswith("anthropic/"):
                    api_model = model  # Already has provider prefix
                else:
                    api_model = f"anthropic/{model}"  # Add prefix if missing
                logger.info(f"Using OpenAICompatEngine for Anthropic model '{model}' via OpenRouter (API: '{api_model}')")
            else:
                raise ValueError(
                    f"Anthropic models require OpenRouter. "
                    f"Set OpenRouter key with: bpui config set api_keys.openrouter YOUR_API_KEY"
                )
        elif provider in ("zai", "moonshot") and provider_key:
            # These providers have OpenAI-compatible APIs
            # Map to their direct API endpoints
            provider_urls = {
                "zai": "https://open.bigmodel.cn/api/paas/v4",
                "moonshot": "https://api.moonshot.cn/v1",
            }
            api_key = provider_key
            base_url = provider_urls.get(provider, "https://openrouter.ai/api/v1")
            api_model = model.split('/')[-1] if '/' in model else model
            logger.info(f"Using OpenAICompatEngine for {provider} direct API model '{model}' (API: '{api_model}')")
        else:
            # No valid API key found
            raise ValueError(
                f"No API key configured for {provider}. "
                f"Set it with: bpui config set api_keys.{provider} YOUR_API_KEY "
                f"(or use OpenRouter: bpui config set api_keys.openrouter YOUR_API_KEY)"
            )

        return OpenAICompatEngine(
            model=api_model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=base_url,
            **kwargs
        )
    else:
        raise ValueError(
            f"Could not create engine for model '{model}'. "
            f"Model name must be in a recognized format, e.g., 'gpt-4', 'gemini-pro', or 'openrouter/provider/model'"
        )


def _create_google_engine(
    config: "Config",
    model: str,
    api_key_override: Optional[str],
    temperature: float,
    max_tokens: int,
    **kwargs
) -> LLMEngine:
    """Create GoogleEngine.

    Args:
        config: Configuration object
        model: Model name
        api_key_override: Optional API key override
        temperature: Temperature setting
        max_tokens: Max tokens setting
        **kwargs: Additional engine parameters

    Returns:
        GoogleEngine

    Raises:
        ImportError: If Google SDK not installed
    """
    from .google_engine import GoogleEngine, GOOGLE_AVAILABLE

    if not GOOGLE_AVAILABLE:
        raise ImportError(
            "Google Generative AI SDK not installed. "
            "Install with: pip install google-generativeai"
        )

    # Get Google API key
    api_key = api_key_override or config.get_api_key("google")
    if not api_key:
        raise ValueError(
            f"No API key configured for Google. "
            f"Set it with: bpui config set api_keys.google YOUR_API_KEY"
        )

    # Get provider-specific config
    google_config = config.get("google", {})
    if isinstance(google_config, dict):
        kwargs.update(google_config)

    logger.info(f"Using native GoogleEngine for model '{model}'")
    api_model = model[len("google/"):] if model.startswith("google/") else model

    return GoogleEngine(
        model=api_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def _create_openai_engine(
    config: "Config",
    model: str,
    api_key_override: Optional[str],
    temperature: float,
    max_tokens: int,
    **kwargs
) -> LLMEngine:
    """Create OpenAIEngine.

    Args:
        config: Configuration object
        model: Model name
        api_key_override: Optional API key override
        temperature: Temperature setting
        max_tokens: Max tokens setting
        **kwargs: Additional engine parameters

    Returns:
        OpenAIEngine

    Raises:
        ImportError: If OpenAI SDK not installed
    """
    from .openai_engine import OpenAIEngine, OPENAI_AVAILABLE

    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI SDK not installed. "
            "Install with: pip install openai"
        )

    # Get OpenAI API key
    api_key = api_key_override or config.get_api_key("openai")
    if not api_key:
        raise ValueError(
            f"No API key configured for OpenAI. "
            f"Set it with: bpui config set api_keys.openai YOUR_API_KEY"
        )

    # Get provider-specific config
    openai_config = config.get("openai", {})
    if isinstance(openai_config, dict):
        kwargs.update(openai_config)

    logger.info(f"Using native OpenAIEngine for model '{model}'")
    api_model = model[len("openai/"):] if model.startswith("openai/") else model

    return OpenAIEngine(
        model=api_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def get_engine_type(config: "Config", model_override: Optional[str] = None) -> str:
    """Get the engine type that would be used for a given model.

    Useful for UI display without actually creating an engine.

    Args:
        config: Configuration object
        model_override: Optional model name to check

    Returns:
        Engine type name: "GoogleEngine", "OpenAIEngine", "OpenAICompatEngine"
    """
    model = model_override or config.model
    engine_mode = config.get("engine_mode", "auto")

    if engine_mode == "explicit":
        engine_type = config.engine
        if engine_type == "openai_compatible":
            return "OpenAICompatEngine"
        elif engine_type == "google":
            return "GoogleEngine"
        elif engine_type == "openai":
            return "OpenAIEngine"
        else:
            return "UnknownEngine"

    # Auto mode
    provider = detect_provider_from_model(model)

    if provider == "google":
        return "GoogleEngine"
    elif provider == "openai":
        return "OpenAIEngine"
    elif provider in ("openrouter", "anthropic", "deepseek", "zai", "moonshot"):
        return "OpenAICompatEngine"
    else:
        return "UnknownEngine"