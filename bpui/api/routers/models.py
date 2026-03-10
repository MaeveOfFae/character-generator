"""Models router for listing available models per provider with dynamic fetching."""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from functools import lru_cache
import time

router = APIRouter()


class ModelInfo(BaseModel):
    """Information about a model."""
    id: str
    name: str
    provider: str
    context_length: int | None = None
    supports_vision: bool = False
    supports_tools: bool = True


class ModelsResponse(BaseModel):
    """Response for models listing."""
    provider: str
    models: List[ModelInfo]
    cached: bool = False
    error: Optional[str] = None


# Cache for dynamic model lists (refreshed on demand)
_model_cache: Dict[str, tuple[List[ModelInfo], float]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour

# Fallback static models when API is unavailable
FALLBACK_MODELS: Dict[str, List[ModelInfo]] = {
    "openai": [
        ModelInfo(id="gpt-4o", name="GPT-4o", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="gpt-4-turbo", name="GPT-4 Turbo", provider="openai", context_length=128000, supports_vision=True),
        ModelInfo(id="o1", name="o1", provider="openai", context_length=200000, supports_tools=False),
        ModelInfo(id="o1-mini", name="o1 Mini", provider="openai", context_length=128000, supports_tools=False),
    ],
    "google": [
        ModelInfo(id="gemini-2.0-flash", name="Gemini 2.0 Flash", provider="google", context_length=1000000, supports_vision=True),
        ModelInfo(id="gemini-1.5-pro", name="Gemini 1.5 Pro", provider="google", context_length=2000000, supports_vision=True),
        ModelInfo(id="gemini-1.5-flash", name="Gemini 1.5 Flash", provider="google", context_length=1000000, supports_vision=True),
    ],
    "openrouter": [
        ModelInfo(id="openrouter/openai/gpt-4o", name="GPT-4o (OpenRouter)", provider="openrouter", context_length=128000),
        ModelInfo(id="openrouter/openai/gpt-4o-mini", name="GPT-4o Mini (OpenRouter)", provider="openrouter", context_length=128000),
        ModelInfo(id="openrouter/anthropic/claude-3.5-sonnet", name="Claude 3.5 Sonnet (OpenRouter)", provider="openrouter", context_length=200000),
        ModelInfo(id="openrouter/anthropic/claude-3-opus", name="Claude 3 Opus (OpenRouter)", provider="openrouter", context_length=200000),
        ModelInfo(id="openrouter/google/gemini-2.0-flash-exp", name="Gemini 2.0 Flash (OpenRouter)", provider="openrouter", context_length=1000000),
        ModelInfo(id="openrouter/meta-llama/llama-3.3-70b-instruct", name="Llama 3.3 70B (OpenRouter)", provider="openrouter", context_length=128000),
        ModelInfo(id="openrouter/deepseek/deepseek-chat", name="DeepSeek Chat (OpenRouter)", provider="openrouter", context_length=64000),
    ],
    "deepseek": [
        ModelInfo(id="deepseek/deepseek-chat", name="DeepSeek Chat", provider="deepseek", context_length=64000),
        ModelInfo(id="deepseek/deepseek-reasoner", name="DeepSeek Reasoner", provider="deepseek", context_length=64000),
    ],
    "zai": [
        ModelInfo(id="zai/glm-4-plus", name="GLM-4 Plus", provider="zai", context_length=128000),
        ModelInfo(id="zai/glm-4-0520", name="GLM-4 0520", provider="zai", context_length=128000),
        ModelInfo(id="zai/glm-4-air", name="GLM-4 Air", provider="zai", context_length=128000),
        ModelInfo(id="zai/glm-4-airx", name="GLM-4 AirX", provider="zai", context_length=8192),
        ModelInfo(id="zai/glm-4-flash", name="GLM-4 Flash", provider="zai", context_length=128000),
    ],
    "moonshot": [
        ModelInfo(id="moonshot-v1-8k", name="Moonshot V1 8K", provider="moonshot", context_length=8192),
        ModelInfo(id="moonshot-v1-32k", name="Moonshot V1 32K", provider="moonshot", context_length=32768),
        ModelInfo(id="moonshot-v1-128k", name="Moonshot V1 128K", provider="moonshot", context_length=131072),
    ],
}

SUPPORTED_PROVIDERS = list(FALLBACK_MODELS.keys())


def _get_api_key(provider: str, request: Request) -> Optional[str]:
    """Get API key for a provider from browser-provided request headers."""
    from bpui.api.byok import get_request_api_keys

    return get_request_api_keys(request).get(provider)


async def _fetch_openai_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from OpenAI API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.openai.com/v1/models", headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"OpenAI API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        # Filter to relevant models
        if any(prefix in model_id for prefix in ["gpt-", "o1-", "o1"]):
            # Estimate context length based on model name
            context_length = 128000
            if "gpt-4" in model_id or "gpt-4o" in model_id:
                context_length = 128000
            elif "o1" in model_id and "mini" not in model_id:
                context_length = 200000

            models.append(ModelInfo(
                id=model_id,
                name=model_id.upper().replace("-", " "),
                provider="openai",
                context_length=context_length,
                supports_vision="gpt-4" in model_id or "gpt-4o" in model_id,
                supports_tools="o1" not in model_id,
            ))

    return sorted(models, key=lambda m: m.id)


async def _fetch_google_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Google API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("models", []):
        name = model.get("name", "").replace("models/", "")
        # Filter to Gemini models
        if "gemini" in name.lower():
            # Extract context length from description if available
            context_length = 1000000  # Default for Gemini
            if "1.5-pro" in name:
                context_length = 2000000

            models.append(ModelInfo(
                id=name,
                name=model.get("displayName", name),
                provider="google",
                context_length=context_length,
                supports_vision=True,
                supports_tools=True,
            ))

    return sorted(models, key=lambda m: m.id)


async def _fetch_openrouter_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from OpenRouter API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://openrouter.ai/api/v1/models", headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"OpenRouter API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        # Prefix with openrouter/ for consistency
        prefixed_id = f"openrouter/{model_id}"

        # Extract context length
        context_length = model.get("context_length")
        if not context_length:
            # Try to get from top_provider
            context_length = model.get("top_provider", {}).get("max_context_length")

        models.append(ModelInfo(
            id=prefixed_id,
            name=model.get("name", model_id),
            provider="openrouter",
            context_length=context_length,
            supports_vision=model.get("architecture", {}).get("modality") in ["text+image->text", "image->text"],
            supports_tools=True,  # Most OpenRouter models support tools
        ))

    # Sort by popularity or name
    return sorted(models, key=lambda m: m.name.lower())


async def _fetch_deepseek_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from DeepSeek API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.deepseek.com/models", headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"DeepSeek API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        # Prefix with deepseek/ for consistency
        prefixed_id = f"deepseek/{model_id}"

        models.append(ModelInfo(
            id=prefixed_id,
            name=model.get("id", model_id).upper().replace("-", " "),
            provider="deepseek",
            context_length=64000,  # DeepSeek default
            supports_vision=False,
            supports_tools=True,
        ))

    return sorted(models, key=lambda m: m.id)


async def _fetch_zai_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from Zhipu AI (GLM) API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://open.bigmodel.cn/api/paas/v4/models", headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Zhipu AI API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")
        prefixed_id = f"zai/{model_id}"

        models.append(ModelInfo(
            id=prefixed_id,
            name=model.get("owned_by", model_id).upper(),
            provider="zai",
            context_length=model.get("context_length", 128000),
            supports_vision="glm-4v" in model_id.lower(),
            supports_tools=True,
        ))

    return sorted(models, key=lambda m: m.id)


async def _fetch_moonshot_models(api_key: str) -> List[ModelInfo]:
    """Fetch models from Moonshot API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.moonshot.cn/v1/models", headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Moonshot API error: {resp.status}")
            data = await resp.json()

    models = []
    for model in data.get("data", []):
        model_id = model.get("id", "")

        # Determine context length from model name
        context_length = 8192
        if "32k" in model_id.lower():
            context_length = 32768
        elif "128k" in model_id.lower():
            context_length = 131072

        models.append(ModelInfo(
            id=model_id,  # Moonshot models don't need prefix
            name=model.get("owned_by", model_id).upper() or "Moonshot V1",
            provider="moonshot",
            context_length=context_length,
            supports_vision=False,
            supports_tools=True,
        ))

    return sorted(models, key=lambda m: m.id)


async def _fetch_provider_models(provider: str, request: Request) -> tuple[List[ModelInfo], Optional[str]]:
    """Fetch models from a provider's API.

    Returns tuple of (models, error_message).
    """
    api_key = _get_api_key(provider, request)

    if not api_key:
        return FALLBACK_MODELS.get(provider, []), f"No API key configured for {provider}. Using fallback models."

    try:
        if provider == "openai":
            models = await _fetch_openai_models(api_key)
        elif provider == "google":
            models = await _fetch_google_models(api_key)
        elif provider == "openrouter":
            models = await _fetch_openrouter_models(api_key)
        elif provider == "deepseek":
            models = await _fetch_deepseek_models(api_key)
        elif provider == "zai":
            models = await _fetch_zai_models(api_key)
        elif provider == "moonshot":
            models = await _fetch_moonshot_models(api_key)
        else:
            return FALLBACK_MODELS.get(provider, []), f"Unknown provider: {provider}"

        return models, None
    except Exception as e:
        return FALLBACK_MODELS.get(provider, []), f"Failed to fetch models: {str(e)}. Using fallback models."


@router.get("/{provider}", response_model=ModelsResponse)
async def get_models(provider: str, request: Request, refresh: bool = False):
    """Get available models for a provider.

    Args:
        provider: Provider name (openai, google, openrouter, deepseek, zai, moonshot)
        refresh: If True, bypass cache and fetch fresh models from API
    """
    provider_lower = provider.lower()

    if provider_lower not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider: {provider}. Available: {SUPPORTED_PROVIDERS}"
        )

    # Check cache
    cached = False
    if not refresh and provider_lower in _model_cache:
        cached_models, cache_time = _model_cache[provider_lower]
        if time.time() - cache_time < CACHE_TTL_SECONDS:
            cached = True
            return ModelsResponse(
                provider=provider_lower,
                models=cached_models,
                cached=True,
            )

    # Fetch models
    models, error = await _fetch_provider_models(provider_lower, request)

    # Update cache
    if models and not error:
        _model_cache[provider_lower] = (models, time.time())

    return ModelsResponse(
        provider=provider_lower,
        models=models,
        cached=False,
        error=error,
    )


@router.post("/{provider}/refresh")
async def refresh_models(provider: str, request: Request):
    """Refresh model list from provider API.

    Forces a fresh fetch from the provider's API, bypassing the cache.
    """
    provider_lower = provider.lower()

    if provider_lower not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider: {provider}. Available: {SUPPORTED_PROVIDERS}"
        )

    # Force refresh
    models, error = await _fetch_provider_models(provider_lower, request)

    # Update cache
    if models and not error:
        _model_cache[provider_lower] = (models, time.time())

    return {
        "status": "refreshed" if not error else "partial",
        "provider": provider_lower,
        "model_count": len(models),
        "error": error,
    }


@router.get("/")
async def list_providers():
    """List all supported providers."""
    return {
        "providers": SUPPORTED_PROVIDERS,
        "description": {
            "openai": "OpenAI GPT models (gpt-4, gpt-4o, o1, etc.)",
            "google": "Google Gemini models (gemini-1.5-pro, gemini-2.0-flash, etc.)",
            "openrouter": "OpenRouter - access to multiple providers through one API",
            "deepseek": "DeepSeek models (deepseek-chat, deepseek-reasoner)",
            "zai": "Zhipu AI GLM models (GLM-4 series)",
            "moonshot": "Moonshot AI models (moonshot-v1 series)",
        },
    }
