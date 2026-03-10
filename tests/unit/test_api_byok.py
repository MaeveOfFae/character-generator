import base64
import json

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from bpui.api.byok import API_KEYS_HEADER, build_request_config, get_request_api_keys
from bpui.api.routers.config import router as config_router
from bpui.core.config import Config


def _encode_api_keys(payload: dict[str, str]) -> dict[str, str]:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return {API_KEYS_HEADER: encoded}


def _make_config(data: dict) -> Config:
    config = Config()
    config._data = data.copy()
    return config


def test_get_request_api_keys_decodes_valid_header():
    app = FastAPI()

    @app.get("/")
    async def read_root(request: Request):
        return get_request_api_keys(request)

    client = TestClient(app)
    response = client.get("/", headers=_encode_api_keys({"openai": " sk-test ", "google": ""}))

    assert response.status_code == 200
    assert response.json() == {"openai": "sk-test"}


def test_build_request_config_uses_browser_keys_only(monkeypatch):
    import bpui.core.config as config_module

    base_config = _make_config(
        {
            "model": "openrouter/openai/gpt-4o-mini",
            "api_keys": {"openai": "server-openai-key"},
            "api_key": "legacy-server-key",
            "api_key_env": "OPENAI_API_KEY",
            "temperature": 0.7,
            "max_tokens": 4096,
            "engine": "openai_compatible",
        }
    )
    monkeypatch.setattr(config_module, "load_config", lambda: base_config)

    app = FastAPI()

    @app.get("/")
    async def read_root(request: Request):
        return build_request_config(request).to_dict()

    client = TestClient(app)
    response = client.get("/", headers=_encode_api_keys({"openrouter": "browser-key"}))

    assert response.status_code == 200
    data = response.json()
    assert data["api_keys"] == {"openrouter": "browser-key"}
    assert data["api_key"] == ""
    assert data["api_key_env"] == ""


def test_config_routes_scrub_and_ignore_api_keys(monkeypatch):
    import bpui.core.config as config_module
    import bpui.api.routers.config as config_router_module

    config = _make_config(
        {
            "engine": "openai",
            "engine_mode": "auto",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4096,
            "api_keys": {"openai": "server-key"},
            "api_key": "legacy-server-key",
            "api_key_env": "OPENAI_API_KEY",
            "batch": {"max_concurrent": 3, "rate_limit_delay": 1.0},
            "theme_name": "dark",
            "theme": {},
        }
    )
    save_calls: list[bool] = []

    monkeypatch.setattr(config_module, "load_config", lambda: config)
    monkeypatch.setattr(config_module, "save_config", lambda: save_calls.append(True))
    monkeypatch.setattr(config_router_module, "AVAILABLE_PROVIDERS", ["openai", "google"])

    app = FastAPI()
    app.include_router(config_router, prefix="/config")
    client = TestClient(app)

    get_response = client.get("/config")
    assert get_response.status_code == 200
    assert get_response.json()["api_keys"] == {}

    update_response = client.post(
        "/config",
        json={"model": "gpt-4o", "api_keys": {"openai": "browser-key"}},
    )

    assert update_response.status_code == 200
    assert update_response.json()["api_keys"] == {}
    assert config.get("model") == "gpt-4o"
    assert config.get("api_keys") == {"openai": "server-key"}
    assert save_calls == [True]


def test_connection_requires_browser_key(monkeypatch):
    import bpui.core.config as config_module
    import bpui.llm.factory as factory_module

    config = _make_config(
        {
            "engine": "openai",
            "engine_mode": "auto",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4096,
            "api_keys": {"openai": "server-key"},
            "api_key": "legacy-server-key",
            "api_key_env": "OPENAI_API_KEY",
            "batch": {"max_concurrent": 3, "rate_limit_delay": 1.0},
            "theme_name": "dark",
            "theme": {},
        }
    )
    captured_keys: list[str | None] = []

    class FakeEngine:
        async def test_connection(self):
            return {"success": True}

    def fake_create_engine(request_config):
        captured_keys.append(request_config.get_api_key("openai"))
        return FakeEngine()

    monkeypatch.setattr(config_module, "load_config", lambda: config)
    monkeypatch.setattr(factory_module, "create_engine", fake_create_engine)

    app = FastAPI()
    app.include_router(config_router, prefix="/config")
    client = TestClient(app)

    missing_key_response = client.post("/config/test", json={"provider": "openai"})
    assert missing_key_response.status_code == 200
    assert missing_key_response.json()["success"] is False
    assert "No API key provided" in missing_key_response.json()["error"]
    assert captured_keys == []

    success_response = client.post(
        "/config/test",
        json={"provider": "openai"},
        headers=_encode_api_keys({"openai": "browser-key"}),
    )
    assert success_response.status_code == 200
    assert success_response.json()["success"] is True
    assert captured_keys == ["browser-key"]