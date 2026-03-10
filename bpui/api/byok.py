"""Bring-your-own-key helpers for web API requests."""

from __future__ import annotations

import base64
import json
from typing import Any

from fastapi import Request


API_KEYS_HEADER = "X-BPUI-API-KEYS"


def get_request_api_keys(request: Request | None) -> dict[str, str]:
    """Extract browser-provided API keys from the request header."""
    if request is None:
        return {}

    encoded = request.headers.get(API_KEYS_HEADER, "").strip()
    if not encoded:
        return {}

    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True).decode("utf-8")
        payload = json.loads(raw)
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}

    return {
        key: value.strip()
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str) and value.strip()
    }


def build_request_config(request: Request):
    """Build a config object for web requests using browser-provided keys only."""
    from bpui.core.config import Config, load_config

    base_config = load_config()
    config = Config()
    config._data = base_config.to_dict().copy()
    config.set("api_keys", get_request_api_keys(request))
    config.set("api_key", "")
    config.set("api_key_env", "")
    return config


def scrub_api_keys(config_data: dict[str, Any]) -> dict[str, Any]:
    """Remove API key material from config responses returned to the web app."""
    sanitized = config_data.copy()
    sanitized["api_keys"] = {}
    sanitized["api_key"] = ""
    sanitized["api_key_env"] = ""
    return sanitized