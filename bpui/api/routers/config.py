"""Configuration router with persistent storage."""

import io
import json
import time
from typing import Dict, Any
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from ..schemas.config import (
    ConfigResponse,
    ConfigUpdate,
    ConnectionTestRequest,
    ConnectionTestResult,
    ThemePresetCreate,
    ThemePresetUpdate,
    ThemeDuplicateRequest,
    ThemeRenameRequest,
    ThemePresetResponse,
    ThemeColorsResponse,
)

router = APIRouter()

AVAILABLE_PROVIDERS = ["openai", "google", "openrouter", "deepseek", "zai", "moonshot"]


def _config_to_response(config_data: Dict[str, Any]) -> ConfigResponse:
    """Convert config dict to response model."""
    from bpui.api.byok import scrub_api_keys

    config_data = scrub_api_keys(config_data)
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
        author=theme.author,
        tags=theme.tags,
        based_on=theme.based_on,
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
        if key == "api_keys":
            continue
        if value is not None:
            config.set(key, value)

    # Persist changes
    save_config()

    return _config_to_response(config.to_dict())


@router.get("/themes", response_model=list[ThemePresetResponse])
async def list_themes():
    """List available theme presets and resolved palettes."""
    from bpui.core.theme import list_theme_presets

    return [_theme_to_response(theme) for theme in list_theme_presets()]


@router.post("/themes", response_model=ThemePresetResponse)
async def create_theme(request: ThemePresetCreate):
    """Create a reusable custom theme preset."""
    from bpui.core.theme import create_custom_theme

    try:
        theme = create_custom_theme(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            based_on=request.based_on,
            colors=request.colors.model_dump(),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _theme_to_response(theme)


@router.get("/themes/{theme_name}/export")
async def export_theme_preset(theme_name: str):
    """Export a theme preset as a portable JSON file."""
    from bpui.core.theme import get_theme

    try:
        theme = get_theme(theme_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    payload = {
        "version": 1,
        "kind": "character-generator-theme",
        "theme": {
            "name": theme.name,
            "display_name": theme.display_name,
            "description": theme.description,
            "author": theme.author,
            "tags": theme.tags,
            "based_on": theme.based_on,
            "colors": theme.to_dict()["colors"],
        },
    }
    content = json.dumps(payload, indent=2).encode("utf-8")
    filename = f"{theme.name}.theme.json"

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        },
    )


@router.post("/themes/import", response_model=ThemePresetResponse)
async def import_theme_preset(
    file: UploadFile = File(...),
    conflict_strategy: str = Form("reject"),
    target_name: str | None = Form(None),
):
    """Import a theme preset from a portable JSON file."""
    from bpui.core.theme import import_theme_definition

    try:
        raw = await file.read()
        payload = json.loads(raw.decode("utf-8"))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Invalid theme file: {error}") from error

    theme_payload = payload.get("theme") if isinstance(payload, dict) and "theme" in payload else payload
    if not isinstance(theme_payload, dict):
        raise HTTPException(status_code=400, detail="Theme import payload is missing a theme object")

    name = theme_payload.get("name")
    display_name = theme_payload.get("display_name") or theme_payload.get("displayName")
    description = theme_payload.get("description", "")
    author = theme_payload.get("author", "")
    tags = theme_payload.get("tags", [])
    based_on = theme_payload.get("based_on") or theme_payload.get("basedOn") or ""
    colors = theme_payload.get("colors")

    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=400, detail="Imported theme is missing a valid name")
    if not isinstance(display_name, str) or not display_name.strip():
        raise HTTPException(status_code=400, detail="Imported theme is missing a valid display_name")
    if not isinstance(author, str):
        raise HTTPException(status_code=400, detail="Imported theme author must be a string")
    if not isinstance(tags, list):
        raise HTTPException(status_code=400, detail="Imported theme tags must be a list")
    if not isinstance(based_on, str):
        raise HTTPException(status_code=400, detail="Imported theme based_on must be a string")
    if not isinstance(colors, dict):
        raise HTTPException(status_code=400, detail="Imported theme is missing a colors object")

    try:
        theme = import_theme_definition(
            name=name,
            display_name=display_name,
            description=description,
            author=author,
            tags=tags,
            based_on=based_on,
            colors=colors,
            conflict_strategy=conflict_strategy,
            target_name=target_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _theme_to_response(theme)


@router.put("/themes/{theme_name}", response_model=ThemePresetResponse)
async def update_theme(theme_name: str, request: ThemePresetUpdate):
    """Update a reusable custom theme preset."""
    from bpui.core.theme import update_custom_theme

    try:
        theme = update_custom_theme(
            name=theme_name,
            display_name=request.display_name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            based_on=request.based_on,
            colors=request.colors.model_dump() if request.colors else None,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _theme_to_response(theme)


@router.post("/themes/{theme_name}/duplicate", response_model=ThemePresetResponse)
async def duplicate_theme_preset(theme_name: str, request: ThemeDuplicateRequest):
    """Duplicate any theme into a new reusable custom preset."""
    from bpui.core.theme import duplicate_theme

    try:
        theme = duplicate_theme(
            name=theme_name,
            new_name=request.new_name,
            display_name=request.display_name,
            description=request.description,
            author=request.author,
            tags=request.tags,
            based_on=request.based_on,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return _theme_to_response(theme)


@router.post("/themes/{theme_name}/rename", response_model=ThemePresetResponse)
async def rename_theme_preset(theme_name: str, request: ThemeRenameRequest):
    """Rename a reusable custom theme preset."""
    from bpui.core.theme import rename_custom_theme
    from bpui.core.config import load_config, save_config

    try:
        theme = rename_custom_theme(
            name=theme_name,
            new_name=request.new_name,
            display_name=request.display_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    config = load_config()
    if config.get("theme_name") == theme_name:
        config.set("theme_name", theme.name)
        save_config()

    return _theme_to_response(theme)


@router.delete("/themes/{theme_name}")
async def delete_theme_preset(theme_name: str):
    """Delete a reusable custom theme preset."""
    from bpui.core.theme import delete_custom_theme
    from bpui.core.config import load_config, save_config

    try:
        delete_custom_theme(theme_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    config = load_config()
    if config.get("theme_name") == theme_name:
        config.set("theme_name", "dark")
        config.set("theme", {})
        save_config()

    return {"status": "deleted", "name": theme_name}


@router.post("/test", response_model=ConnectionTestResult)
async def test_connection(request: ConnectionTestRequest, http_request: Request):
    """Test API connection for a provider using stored API keys."""
    try:
        from bpui.llm.factory import create_engine
        from bpui.api.byok import build_request_config

        # Load a request-scoped config that only uses browser-provided keys.
        config = build_request_config(http_request)

        # Determine which API key to use based on provider
        provider_key = config.get_api_key(request.provider)

        if not provider_key:
            return ConnectionTestResult(
                success=False,
                error=f"No API key provided for {request.provider}. Add your key in the browser Settings panel.",
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
