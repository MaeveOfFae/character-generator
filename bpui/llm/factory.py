"""Engine factory for creating LLM engines based on model and configuration."""

import logging
from typing import Optional, TYPE_CHECKING

from .base import LLMEngine

if TYPE_CHECKING:
    from ..config import Config

logger = logging.getLogger(__name__)


def detect_provider_from_model(model: str) -> str:
    """Detect provider from model name.

    Args:
        model: Model name (e.g., "gpt-4", "gemini-1.5-pro", "openai/gpt-4")

    Returns:
        Provider name: "google", "openai", "litellm", or "unknown"

    Examples:
        "gpt-4" -> "openai"
        "gpt-4-turbo" -> "openai"
        "o1-preview" -> "openai"
        "gemini-1.5-pro" -> "google"
        "gemini-pro" -> "google"
        "openai/gpt-4" -> "litellm" (slash indicates LiteLLM format)
        "anthropic/claude-3" -> "litellm"
        "random-model" -> "unknown"
    """
    # If model has slash, it's LiteLLM format provider/model
    if "/" in model:
        return "litellm"

    # Auto-detect based on model name prefix
    model_lower = model.lower()

    # OpenAI models
    if model_lower.startswith(("gpt-", "o1-", "o1")):
        return "openai"

    # Google models
    if model_lower.startswith("gemini"):
        return "google"

    # Unknown - will fall back to LiteLLM or raise error
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
    - Fallback logic if native SDK not installed

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
        ImportError: If native SDK required but not installed (with fallback suggestion)

    Examples:
        # Auto mode (default):
        engine = create_engine(config)  # Uses config.model to auto-detect

        # With overrides:
        engine = create_engine(config, model_override="gpt-4", temperature=0.8)

        # Explicit mode (honors config.engine):
        # config.engine_mode = "explicit"
        # config.engine = "litellm"
        engine = create_engine(config)  # Forces LiteLLM regardless of model
    """
    from .litellm_engine import LiteLLMEngine, LITELLM_AVAILABLE
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

        if engine_type == "litellm":
            if not LITELLM_AVAILABLE:
                raise ImportError(
                    "LiteLLM not installed. Install with: pip install litellm"
                )
            api_key = api_key_override or config.get_api_key_for_model(model)
            return LiteLLMEngine(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

        elif engine_type == "openai_compatible":
            api_key = api_key_override or config.api_key
            base_url = config.base_url
            if not base_url:
                raise ValueError(
                    "OpenAI-compatible engine requires base_url in config"
                )
            return OpenAICompatEngine(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                base_url=base_url,
                **kwargs
            )

        elif engine_type == "google":
            return _create_google_engine(
                config, model, api_key_override, temperature, max_tokens, **kwargs
            )

        elif engine_type == "openai":
            return _create_openai_engine(
                config, model, api_key_override, temperature, max_tokens, **kwargs
            )

        else:
            raise ValueError(f"Unknown engine type: {engine_type}")

    # Auto mode: detect provider from model name
    provider = detect_provider_from_model(model)
    logger.info(f"Auto-detected provider '{provider}' from model '{model}'")

    if provider == "google":
        return _create_google_engine(
            config, model, api_key_override, temperature, max_tokens, **kwargs
        )

    elif provider == "openai":
        return _create_openai_engine(
            config, model, api_key_override, temperature, max_tokens, **kwargs
        )

    elif provider == "litellm" or provider == "unknown":
        # Fall back to LiteLLM for slash format or unknown models
        if not LITELLM_AVAILABLE:
            raise ImportError(
                f"LiteLLM not installed and no native engine available for model '{model}'. "
                f"Install with: pip install litellm"
            )

        api_key = api_key_override or config.get_api_key_for_model(model)
        logger.info(f"Using LiteLLM engine for model '{model}'")
        return LiteLLMEngine(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    else:
        raise ValueError(f"Could not create engine for provider: {provider}")


def _create_google_engine(
    config: "Config",
    model: str,
    api_key_override: Optional[str],
    temperature: float,
    max_tokens: int,
    **kwargs
) -> LLMEngine:
    """Create GoogleEngine with fallback to LiteLLM if not available.

    Args:
        config: Configuration object
        model: Model name
        api_key_override: Optional API key override
        temperature: Temperature setting
        max_tokens: Max tokens setting
        **kwargs: Additional engine parameters

    Returns:
        GoogleEngine or LiteLLM fallback

    Raises:
        ImportError: If neither Google SDK nor LiteLLM available
    """
    try:
        from .google_engine import GoogleEngine, GOOGLE_AVAILABLE

        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI SDK not available")

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
        return GoogleEngine(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    except (ImportError, ValueError) as e:
        # Fall back to LiteLLM if available
        logger.warning(f"Could not create GoogleEngine: {e}")
        logger.info("Attempting fallback to LiteLLM...")

        from .litellm_engine import LiteLLMEngine, LITELLM_AVAILABLE

        if not LITELLM_AVAILABLE:
            raise ImportError(
                f"Google SDK not installed and LiteLLM fallback not available. "
                f"Install with: pip install google-generativeai"
            ) from e

        # Convert model to LiteLLM format if needed
        litellm_model = f"google/{model}" if "/" not in model else model
        api_key = api_key_override or config.get_api_key("google")

        logger.info(f"Using LiteLLM fallback for Google model '{litellm_model}'")
        return LiteLLMEngine(
            model=litellm_model,
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
    """Create OpenAIEngine with fallback to LiteLLM if not available.

    Args:
        config: Configuration object
        model: Model name
        api_key_override: Optional API key override
        temperature: Temperature setting
        max_tokens: Max tokens setting
        **kwargs: Additional engine parameters

    Returns:
        OpenAIEngine or LiteLLM fallback

    Raises:
        ImportError: If neither OpenAI SDK nor LiteLLM available
    """
    try:
        from .openai_engine import OpenAIEngine, OPENAI_AVAILABLE

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available")

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
        return OpenAIEngine(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    except (ImportError, ValueError) as e:
        # Fall back to LiteLLM if available
        logger.warning(f"Could not create OpenAIEngine: {e}")
        logger.info("Attempting fallback to LiteLLM...")

        from .litellm_engine import LiteLLMEngine, LITELLM_AVAILABLE

        if not LITELLM_AVAILABLE:
            raise ImportError(
                f"OpenAI SDK not installed and LiteLLM fallback not available. "
                f"Install with: pip install openai"
            ) from e

        # Convert model to LiteLLM format if needed
        litellm_model = f"openai/{model}" if "/" not in model else model
        api_key = api_key_override or config.get_api_key("openai")

        logger.info(f"Using LiteLLM fallback for OpenAI model '{litellm_model}'")
        return LiteLLMEngine(
            model=litellm_model,
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
        Engine type name: "GoogleEngine", "OpenAIEngine", "LiteLLMEngine", "OpenAICompatEngine"
    """
    model = model_override or config.model
    engine_mode = config.get("engine_mode", "auto")

    if engine_mode == "explicit":
        engine_type = config.engine
        if engine_type == "litellm":
            return "LiteLLMEngine"
        elif engine_type == "openai_compatible":
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
        try:
            from .google_engine import GOOGLE_AVAILABLE
            return "GoogleEngine" if GOOGLE_AVAILABLE else "LiteLLMEngine (fallback)"
        except ImportError:
            return "LiteLLMEngine (fallback)"

    elif provider == "openai":
        try:
            from .openai_engine import OPENAI_AVAILABLE
            return "OpenAIEngine" if OPENAI_AVAILABLE else "LiteLLMEngine (fallback)"
        except ImportError:
            return "LiteLLMEngine (fallback)"

    elif provider == "litellm":
        return "LiteLLMEngine"

    else:
        return "LiteLLMEngine (fallback)"
