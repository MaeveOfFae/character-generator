import asyncio
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from bpui.api.routers.generation import generate_batch
from bpui.api.routers.offspring import router as offspring_router
from bpui.api.schemas.generation import GenerateBatchRequest


async def _collect_streaming_body(response) -> str:
    chunks: list[str] = []
    async for chunk in response.body_iterator:
        if isinstance(chunk, bytes):
            chunks.append(chunk.decode("utf-8"))
        else:
            chunks.append(chunk)
    return "".join(chunks)


class _FakeBatchEngine:
    async def generate_stream(self, system_prompt: str, user_prompt: str):
        yield "generated output"


class _FakeOffspringEngine:
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "generated output"


def test_offspring_route_accepts_json_body_and_emits_draft_id(tmp_path, monkeypatch):
    import bpui.api.routers.offspring as offspring_module

    parent1_dir = tmp_path / "parent_one"
    parent2_dir = tmp_path / "parent_two"
    child_dir = tmp_path / "child_draft"
    parent1_dir.mkdir()
    parent2_dir.mkdir()
    child_dir.mkdir()

    monkeypatch.setattr(
        offspring_module,
        "_find_draft_dir",
        lambda draft_id: {
            "parent-1": parent1_dir,
            "parent-2": parent2_dir,
        }[draft_id],
    )
    monkeypatch.setattr("bpui.core.config.load_config", lambda: SimpleNamespace(model="test/model"))
    monkeypatch.setattr("bpui.llm.factory.create_engine", lambda config: _FakeOffspringEngine())
    monkeypatch.setattr(
        "bpui.core.prompting.build_asset_prompt",
        lambda asset_name, offspring_seed, mode, assets: ("system", "user"),
    )
    monkeypatch.setattr("bpui.core.parse_blocks.extract_single_asset", lambda output, asset_name: "name: Child")
    monkeypatch.setattr("bpui.core.parse_blocks.extract_character_name", lambda content: "Child")
    monkeypatch.setattr(
        "bpui.utils.file_io.pack_io.load_draft",
        lambda draft_path: {"character_sheet": f"name: {draft_path.name}"},
    )
    monkeypatch.setattr(
        "bpui.utils.file_io.pack_io.create_draft_dir",
        lambda *args, **kwargs: child_dir,
    )
    monkeypatch.setattr("bpui.utils.topological_sort.topological_sort", lambda assets: ["character_sheet"])

    class FakeTemplateManager:
        def get_template(self, name):
            return SimpleNamespace(name=name, assets=[SimpleNamespace(name="character_sheet")])

    monkeypatch.setattr("bpui.features.templates.templates.TemplateManager", FakeTemplateManager)

    app = FastAPI()
    app.include_router(offspring_router, prefix="/offspring")
    client = TestClient(app)

    response = client.post(
        "/offspring",
        json={
            "parent1_id": "parent-1",
            "parent2_id": "parent-2",
            "mode": "SFW",
            "seed": "child concept",
        },
    )

    assert response.status_code == 200
    assert "event: complete" in response.text
    assert '"draft_id": "child_draft"' in response.text


def test_generate_batch_stream_emits_completion_for_each_seed(tmp_path, monkeypatch):
    monkeypatch.setattr("bpui.core.config.load_config", lambda: SimpleNamespace(model="test/model"))
    monkeypatch.setattr("bpui.llm.factory.create_engine", lambda config: _FakeBatchEngine())
    monkeypatch.setattr(
        "bpui.core.prompting.build_orchestrator_prompt",
        lambda seed, mode, template=None: ("system", f"user:{seed}"),
    )
    monkeypatch.setattr(
        "bpui.core.parse_blocks.parse_blueprint_output",
        lambda full_response, template_obj: {"character_sheet": "name: Batch Character"},
    )
    monkeypatch.setattr("bpui.core.parse_blocks.extract_character_name", lambda content: "Batch Character")

    def fake_create_draft_dir(*args, **kwargs):
        draft_dir = tmp_path / kwargs["seed"].replace(" ", "_")
        draft_dir.mkdir(exist_ok=True)
        return draft_dir

    monkeypatch.setattr("bpui.utils.file_io.pack_io.create_draft_dir", fake_create_draft_dir)

    response = asyncio.run(
        generate_batch(
            GenerateBatchRequest(
                seeds=["first seed", "second seed"],
                mode="SFW",
                parallel=True,
                max_concurrent=2,
            )
        )
    )
    body = asyncio.run(_collect_streaming_body(response))

    assert body.count("event: batch_start") == 2
    assert body.count("event: batch_complete") == 2
    assert '"draft_id": "first_seed"' in body
    assert '"draft_id": "second_seed"' in body
    assert 'event: complete\ndata: {"total": 2}' in body