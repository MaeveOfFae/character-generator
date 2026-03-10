import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bpui.api.routers.config import router as config_router


def _theme_payload(name: str, display_name: str, colors: dict[str, str]) -> dict:
    return {
        "version": 1,
        "kind": "character-generator-theme",
        "theme": {
            "name": name,
            "display_name": display_name,
            "description": "Imported theme",
            "author": "Nyx",
            "tags": ["warm", "night"],
            "based_on": "dark",
            "colors": colors,
        },
    }


def test_import_theme_route_supports_rename_on_conflict(monkeypatch):
    import bpui.core.theme as theme_module

    app = FastAPI()
    app.include_router(config_router, prefix="/config")
    client = TestClient(app)

    captured: dict[str, object] = {}

    class ImportedTheme:
        name = "ember_night_2"
        display_name = "Imported Ember"
        description = "Imported theme"
        author = "Nyx"
        tags = ["warm", "night"]
        based_on = "dark"
        is_builtin = False

        def to_dict(self):
            return {
                "colors": {
                    "background": "#111111",
                    "text": "#eeeeee",
                    "accent": "#ff5500",
                    "button": "#222222",
                    "button_text": "#ffffff",
                    "border": "#333333",
                    "highlight": "#444444",
                    "window": "#000000",
                    "tok_brackets": "#aaaaaa",
                    "tok_asterisk": "#bbbbbb",
                    "tok_parentheses": "#cccccc",
                    "tok_double_brackets": "#dddddd",
                    "tok_curly_braces": "#eeeeee",
                    "tok_pipes": "#ffffff",
                    "tok_at_sign": "#121212",
                    "muted_text": "#999999",
                    "surface": "#202020",
                    "success_bg": "#225522",
                    "danger_bg": "#552222",
                    "accent_bg": "#442244",
                    "accent_title": "#ff9900",
                    "success_text": "#66cc66",
                    "error_text": "#ff6666",
                    "warning_text": "#ffcc66",
                    "tui_primary": "#ff5500",
                    "tui_secondary": "#00cccc",
                    "tui_surface": "#202020",
                    "tui_panel": "#2a2a2a",
                    "tui_warning": "#ffaa00",
                    "tui_error": "#ff6666",
                    "tui_success": "#66cc66",
                    "tui_accent": "#ff9900",
                }
            }

    def fake_import_theme_definition(**kwargs):
        captured.update(kwargs)
        return ImportedTheme()

    monkeypatch.setattr(theme_module, "import_theme_definition", fake_import_theme_definition)

    payload = _theme_payload(
        "ember_night",
        "Imported Ember",
        ImportedTheme().to_dict()["colors"],
    )

    response = client.post(
        "/config/themes/import",
        files={"file": ("ember_night.theme.json", json.dumps(payload), "application/json")},
        data={"conflict_strategy": "rename", "target_name": "ember_night_2"},
    )

    assert response.status_code == 200
    assert captured["conflict_strategy"] == "rename"
    assert captured["target_name"] == "ember_night_2"
    assert captured["author"] == "Nyx"
    assert captured["tags"] == ["warm", "night"]
    assert captured["based_on"] == "dark"


def test_import_theme_route_rejects_invalid_payload():
    app = FastAPI()
    app.include_router(config_router, prefix="/config")
    client = TestClient(app)

    response = client.post(
        "/config/themes/import",
        files={"file": ("broken.theme.json", "not-json", "application/json")},
    )

    assert response.status_code == 400
    assert "Invalid theme file" in response.json()["detail"]