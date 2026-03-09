"""Configuration router with persistent storage."""

import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from ..schemas.config import (
    ConfigResponse,
    ConfigUpdate,
    ConnectionTestRequest,
    ConnectionTestResult,
    ThemePresetResponse,
    ThemeColorsResponse,
)

router = APIRouter()

AVAILABLE_PROVIDERS = ["openai", "google", "openrouter", "deepseek", "zai", "moonshot"]


def _config_to_response(config_data: Dict[str, Any]) -> ConfigResponse:
    """Convert config dict to response model."""
    return ConfigResponse(
        engine=config_data.get("engine", "auto"),
        engine_mode=config_data.get("engine_mode", "auto"),
        model=config_data.get("model", "openrouter/openai/gpt-4o-mini"),
        temperature=config_data.get("temperature", 0.7),
        max_tokens=config_data.get("max_tokens", 4096),
        api_keys=config_data.get("api_keys", {}),
        batch=config_data.get("batch", {"max_concurrent": 3, "rate_limit_delay": 1.0}),
        base_url=config_data.get("base_url"),
        theme_name=config_data.get("theme_name", "dark"),
        theme=config_data.get("theme", {}),
        available_providers=AVAILABLE_PROVIDERS,
    )


def _theme_to_response(theme) -> ThemePresetResponse:
    """Convert a ThemeDefinition into the API response shape."""
    return ThemePresetResponse(
        name=theme.name,
        display_name=theme.display_name,
        description=theme.description,
        is_builtin=theme.is_builtin,
        colors=ThemeColorsResponse(**theme.to_dict()["colors"]),
    )


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration from persistent storage."""
    from bpui.core.config import load_config

    config = load_config()
    return _config_to_response(config.to_dict())


@router.post("", response_model=ConfigResponse)
async def update_config(update: ConfigUpdate):
    """Update configuration and persist to storage."""
    from bpui.core.config import load_config, save_config

    config = load_config()
    update_data = update.model_dump(exclude_unset=True)

    # Update config with new values
    for key, value in update_data.items():
        if value is not None:
            config.set(key, value)

    # Persist changes
    save_config()

    return _config_to_response(config.to_dict())


@router.get("/themes", response_model=list[ThemePresetResponse])
async def list_themes():
    """List available theme presets and resolved palettes."""
    from bpui.core.theme import list_available_themes, get_theme

    themes = []
    for theme_name in list_available_themes():
        themes.append(_theme_to_response(get_theme(theme_name)))

    return themes


@router.post("/test", response_model=ConnectionTestResult)
async def test_connection(request: ConnectionTestRequest):
    """Test API connection for a provider using stored API keys."""
    try:
        from bpui.llm.factory import create_engine
        from bpui.core.config import load_config

        # Load current config (has stored API keys)
        config = load_config()

        # Determine which API key to use based on provider
        provider_key = config.get_api_key(request.provider)

        if not provider_key:
            return ConnectionTestResult(
                success=False,
                error=f"No API key configured for {request.provider}. Please add your API key in Settings.",
            )

        # Create a temporary config for testing
        from bpui.core.config import Config as ConfigClass
        test_config = ConfigClass()
        test_config._data = config.to_dict().copy()

        # Set provider-specific settings for the test
        if request.provider == "openrouter":
            test_config.set("engine", "openai_compatible")
            test_config.set("model", request.model or "openrouter/openai/gpt-4o-mini")
            test_config.set("base_url", "https://openrouter.ai/api/v1")
        elif request.provider == "openai":
            test_config.set("engine", "openai")
            test_config.set("model", request.model or "gpt-4o-mini")
            test_config.set("base_url", None)
        elif request.provider == "google":
            test_config.set("engine", "google")
            test_config.set("model", request.model or "gemini-2.0-flash")
            test_config.set("base_url", None)
        elif request.provider == "deepseek":
            test_config.set("engine", "openai_compatible")
            test_config.set("model", request.model or "deepseek/deepseek-chat")
            test_config.set("base_url", "https://api.deepseek.com")
        elif request.provider == "zai":
            test_config.set("engine", "openai_compatible")
            test_config.set("model", request.model or "zai/glm-4")
            test_config.set("base_url", "https://open.bigmodel.cn/api/paas/v4")
        elif request.provider == "moonshot":
            test_config.set("engine", "openai_compatible")
            test_config.set("model", request.model or "moonshot-v1-8k")
            test_config.set("base_url", "https://api.moonshot.cn/v1")
        else:
            test_config.set("engine", "openai_compatible")
            test_config.set("model", request.model or f"{request.provider}/default")
            if request.base_url:
                test_config.set("base_url", request.base_url)

        # Create engine and test
        start_time = time.time()
        engine = create_engine(test_config)
        result = await engine.test_connection()
        latency_ms = (time.time() - start_time) * 1000

        return ConnectionTestResult(
            success=result.get("success", False),
            latency_ms=latency_ms,
            error=result.get("error"),
            model_info=result.get("model_info"),
        )

    except Exception as e:
        return ConnectionTestResult(
            success=False,
            error=str(e),
        )
