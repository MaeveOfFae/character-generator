import asyncio
from pathlib import Path

from bpui.api.routers.chat import apply_refinement
from bpui.api.routers import drafts as drafts_router
from bpui.api.routers.drafts import update_asset
from bpui.api.routers.validation import _run_validation
from bpui.api.schemas.drafts import AssetUpdate
from bpui.utils.metadata.metadata import DraftMetadata


AKSHO_FILES = [
    "initial_message.md",
    "char_basic_info.md",
    "char_physical.md",
    "char_clothing.md",
    "char_personality.md",
    "char_background.md",
    "system_prompt.md",
    "post_history.md",
]


def _create_aksho_draft(base_dir: Path, draft_name: str = "20260307_203638_test_character") -> Path:
    draft_dir = base_dir / draft_name
    draft_dir.mkdir(parents=True)

    for filename in AKSHO_FILES:
        (draft_dir / filename).write_text(f"content for {filename}", encoding="utf-8")

    DraftMetadata(
        seed="test seed",
        mode="SFW",
        model="test-model",
        character_name="test_character",
        template_name="Official Aksho",
    ).save(draft_dir)

    return draft_dir


def test_template_draft_validation_passes_for_complete_aksho_draft(tmp_path):
    draft_dir = _create_aksho_draft(tmp_path)

    result = _run_validation(draft_dir)

    assert result.success is True
    assert result.exit_code == 0
    assert result.output == "OK\n"


def test_template_draft_validation_reports_missing_required_template_file(tmp_path):
    draft_dir = _create_aksho_draft(tmp_path)
    (draft_dir / "initial_message.md").unlink()

    result = _run_validation(draft_dir)

    assert result.success is False
    assert result.exit_code == 1
    assert "VALIDATION FAILED" in result.output
    assert "Missing required file: initial_message.md" in result.output


def test_update_asset_writes_template_specific_filename(tmp_path, monkeypatch):
    draft_dir = _create_aksho_draft(tmp_path)
    monkeypatch.setattr(drafts_router, "DRAFTS_DIR", tmp_path)

    asyncio.run(update_asset(draft_dir.name, "system_prompt", AssetUpdate(content="updated prompt")))

    assert (draft_dir / "system_prompt.md").read_text(encoding="utf-8") == "updated prompt"
    assert not (draft_dir / "system_prompt.txt").exists()


def test_apply_refinement_writes_template_specific_filename(tmp_path, monkeypatch):
    draft_dir = _create_aksho_draft(tmp_path)
    monkeypatch.setattr(drafts_router, "DRAFTS_DIR", tmp_path)

    result = asyncio.run(apply_refinement(draft_dir.name, "system_prompt", "refined prompt"))

    assert result["status"] == "updated"
    assert (draft_dir / "system_prompt.md").read_text(encoding="utf-8") == "refined prompt"
    assert not (draft_dir / "system_prompt.txt").exists()
