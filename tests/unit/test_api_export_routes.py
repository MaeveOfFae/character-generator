import io
import zipfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bpui.api.routers.export import router as export_router
from bpui.features.export.export_presets import ExportPreset, FieldMapping


def test_text_export_preserves_target_filenames_and_content(monkeypatch, tmp_path):
    import bpui.api.routers.export as export_module

    draft_dir = tmp_path / "draft"
    draft_dir.mkdir()

    preset = ExportPreset(
        name="Custom Text Export",
        format="text",
        description="",
        fields=[
            FieldMapping(asset="system_prompt", target="system_prompt.txt"),
            FieldMapping(asset="intro_page", target="intro_page.md"),
            FieldMapping(asset="suno", target="suno_prompt.txt"),
        ],
    )

    monkeypatch.setattr(export_module, "_find_draft_dir", lambda draft_id: draft_dir)
    monkeypatch.setattr(
        export_module,
        "_load_assets",
        lambda path: {
            "system_prompt": "System prompt body",
            "intro_page": "# Intro page\n\nBody copy",
        },
    )
    monkeypatch.setattr(
        export_module,
        "_load_metadata",
        lambda path: {"character_name": "Export Test"},
    )
    monkeypatch.setattr(export_module, "_resolve_preset", lambda preset_name: (Path("custom.toml"), preset))

    app = FastAPI()
    app.include_router(export_router, prefix="/export")
    client = TestClient(app)

    response = client.post(
        "/export",
        json={
            "draft_id": "draft",
            "preset": "custom",
            "include_metadata": False,
        },
    )

    assert response.status_code == 200

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "system_prompt.txt" in archive.namelist()
        assert "system_prompt.txt.txt" not in archive.namelist()
        assert "suno_prompt.txt" not in archive.namelist()
        assert archive.read("system_prompt.txt").decode("utf-8") == "System prompt body"
        assert archive.read("intro_page.md").decode("utf-8") == "# Intro page\n\nBody copy"


def test_raw_export_uses_current_draft_layout(monkeypatch, tmp_path):
    import bpui.api.routers.export as export_module

    draft_dir = tmp_path / "draft"
    draft_dir.mkdir()
    (draft_dir / "system_prompt.md").write_text("System md", encoding="utf-8")
    (draft_dir / "initial_message.md").write_text("Initial message", encoding="utf-8")

    preset = ExportPreset(
        name="Current Draft Layout",
        format="text",
        description="",
        fields=[FieldMapping(asset="system_prompt", target="system_prompt.txt")],
    )

    monkeypatch.setattr(export_module, "_find_draft_dir", lambda draft_id: draft_dir)
    monkeypatch.setattr(export_module, "_load_assets", lambda path: {"system_prompt": "ignored"})
    monkeypatch.setattr(
        export_module,
        "_load_metadata",
        lambda path: {"character_name": "Template Export", "template_name": "Official Aksho"},
    )
    monkeypatch.setattr(export_module, "_resolve_preset", lambda preset_name: (Path("raw.toml"), preset))

    app = FastAPI()
    app.include_router(export_router, prefix="/export")
    client = TestClient(app)

    response = client.post(
        "/export",
        json={
            "draft_id": "draft",
            "preset": "raw",
            "include_metadata": False,
        },
    )

    assert response.status_code == 200

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert sorted(archive.namelist()) == ["initial_message.md", "system_prompt.md"]
        assert archive.read("system_prompt.md").decode("utf-8") == "System md"
        assert archive.read("initial_message.md").decode("utf-8") == "Initial message"