"""Generation router with SSE streaming."""

import asyncio
import json
import time
from typing import Awaitable, Callable
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..schemas.generation import (
    FinalizeGenerationRequest,
    GenerateAssetRequest,
    GenerateBatchRequest,
    GenerateRequest,
)

router = APIRouter()


def _sse(event: str, payload: dict) -> str:
    """Format a server-sent event payload."""
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


async def _generate_assets_sequential(
    seed: str,
    mode: str,
    template_obj,
    engine,
    on_status: Callable[[dict], Awaitable[None]] | None = None,
    on_asset: Callable[[dict], Awaitable[None]] | None = None,
    on_chunk: Callable[[dict], Awaitable[None]] | None = None,
    on_asset_complete: Callable[[dict], Awaitable[None]] | None = None,
) -> tuple[dict[str, str], str]:
    """Generate assets in dependency order, carrying prior assets forward as context."""
    from bpui.core.prompting import build_asset_prompt
    from bpui.core.parse_blocks import extract_single_asset, extract_character_display_name, infer_character_display_name_from_assets
    from bpui.features.templates.templates import TemplateManager
    from bpui.utils.topological_sort import topological_sort

    async def emit(callback: Callable[[dict], Awaitable[None]] | None, payload: dict) -> None:
        if callback:
            await callback(payload)

    manager = TemplateManager()
    try:
        asset_order = topological_sort(template_obj.assets)
    except ValueError:
        asset_order = [asset.name for asset in template_obj.assets]

    assets: dict[str, str] = {}
    character_name = "unnamed_character"
    total_assets = max(len(asset_order), 1)

    for index, asset_name in enumerate(asset_order):
        progress = index / total_assets
        await emit(
            on_status,
            {
                "stage": "asset_generation",
                "status": "in_progress",
                "asset": asset_name,
                "progress": progress,
            },
        )
        await emit(
            on_asset,
            {
                "name": asset_name,
                "status": "started",
                "progress": progress,
            },
        )

        blueprint_content = manager.get_blueprint_content(template_obj, asset_name)
        if not blueprint_content:
            raise ValueError(
                f"Blueprint for asset '{asset_name}' not found in template '{template_obj.name}'"
            )

        system_prompt, user_prompt = build_asset_prompt(
            asset_name=asset_name,
            seed=seed,
            mode=mode,
            prior_assets=assets,
            blueprint_content=blueprint_content,
        )

        raw_output = ""
        async for chunk in engine.generate_stream(system_prompt, user_prompt):
            raw_output += chunk
            await emit(on_chunk, {"content": chunk, "asset": asset_name})

        asset_content = extract_single_asset(raw_output, asset_name)
        assets[asset_name] = asset_content

        extracted_name = extract_character_display_name(asset_content)
        if extracted_name:
            character_name = extracted_name

        await emit(
            on_asset_complete,
            {
                "name": asset_name,
                "length": len(asset_content),
                "progress": (index + 1) / total_assets,
            },
        )

    return assets, infer_character_display_name_from_assets(assets) or character_name


def _resolve_template(template_name: str | None):
    """Resolve a template, defaulting to the official built-in template."""
    from bpui.features.templates.templates import TemplateManager

    resolved_name = template_name or "V2/V3 Card"
    template_obj = TemplateManager().get_template(resolved_name)
    if not template_obj:
        raise ValueError(f"Template not found: {resolved_name}")
    return template_obj


def _get_asset_order(template_obj) -> list[str]:
    """Return a template's asset order, falling back to declared order on sort failure."""
    from bpui.utils.topological_sort import topological_sort

    try:
        return topological_sort(template_obj.assets)
    except ValueError:
        return [asset.name for asset in template_obj.assets]


def _validate_asset_request(template_obj, asset_name: str, prior_assets: dict[str, str]) -> list[str]:
    """Validate that an asset request has the required prior context."""
    asset_order = _get_asset_order(template_obj)
    if asset_name not in asset_order:
        raise ValueError(f"Asset '{asset_name}' is not part of template '{template_obj.name}'")

    current_index = asset_order.index(asset_name)
    required_prior = asset_order[:current_index]
    missing = [name for name in required_prior if name not in prior_assets]
    return missing


async def _generate_single(seed: str, mode: str, request_config, template: str | None = None):
    """Generate a single character with SSE streaming."""
    start_time = time.time()

    async def event_generator():
        event_queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def run_generation() -> None:
            try:
                from bpui.llm.factory import create_engine
                from bpui.utils.file_io.pack_io import create_draft_dir

                await event_queue.put(_sse("status", {"stage": "initializing", "status": "started"}))

                config = request_config
                engine = create_engine(config)
                template_obj = _resolve_template(template)

                assets, character_name = await _generate_assets_sequential(
                    seed=seed,
                    mode=mode,
                    template_obj=template_obj,
                    engine=engine,
                    on_status=lambda payload: event_queue.put(_sse("status", payload)),
                    on_asset=lambda payload: event_queue.put(_sse("asset", payload)),
                    on_chunk=lambda payload: event_queue.put(_sse("chunk", payload)),
                    on_asset_complete=lambda payload: event_queue.put(_sse("asset_complete", payload)),
                )

                await event_queue.put(_sse("status", {"stage": "saving", "status": "in_progress"}))

                draft_path = create_draft_dir(
                    assets,
                    character_name,
                    seed=seed,
                    mode=mode,
                    model=config.model,
                    template=template_obj,
                )

                duration_ms = (time.time() - start_time) * 1000
                await event_queue.put(_sse("status", {"stage": "complete", "status": "complete"}))
                await event_queue.put(
                    _sse(
                        "complete",
                        {
                            "draft_path": str(draft_path),
                            "draft_id": draft_path.name,
                            "character_name": character_name,
                            "duration_ms": duration_ms,
                        },
                    )
                )
            except Exception as error:
                await event_queue.put(_sse("error", {"error": str(error)}))
            finally:
                await event_queue.put(None)

        task = asyncio.create_task(run_generation())
        try:
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/asset")
async def generate_asset(request: GenerateAssetRequest, http_request: Request):
    """Generate a single asset using the currently approved prior assets as context."""
    from bpui.api.schemas.generation import GenerateAssetResponse
    from bpui.api.byok import build_request_config
    from bpui.core.prompting import build_asset_prompt
    from bpui.core.parse_blocks import extract_single_asset, extract_character_display_name
    from bpui.features.templates.templates import TemplateManager
    from bpui.llm.factory import create_engine

    try:
        template_obj = _resolve_template(request.template)
        missing = _validate_asset_request(template_obj, request.asset_name, request.prior_assets)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required prior assets for {request.asset_name}: {', '.join(missing)}",
            )

        manager = TemplateManager()
        blueprint_content = manager.get_blueprint_content(template_obj, request.asset_name)
        if not blueprint_content:
            raise HTTPException(
                status_code=400,
                detail=f"Blueprint for asset '{request.asset_name}' not found in template '{template_obj.name}'",
            )

        config = build_request_config(http_request)
        engine = create_engine(config)
        system_prompt, user_prompt = build_asset_prompt(
            asset_name=request.asset_name,
            seed=request.seed,
            mode=request.mode,
            prior_assets=request.prior_assets,
            blueprint_content=blueprint_content,
        )

        raw_output = await engine.generate(system_prompt, user_prompt)
        content = extract_single_asset(raw_output, request.asset_name)
        character_name = extract_character_display_name(content)

        return GenerateAssetResponse(
            asset_name=request.asset_name,
            content=content,
            character_name=character_name,
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/finalize")
async def finalize_generation(request: FinalizeGenerationRequest):
    """Persist a fully reviewed draft assembled through per-asset generation."""
    from bpui.api.schemas.generation import GenerationComplete
    from bpui.core.parse_blocks import infer_character_display_name_from_assets
    from bpui.core.config import load_config
    from bpui.utils.file_io.pack_io import create_draft_dir

    start_time = time.time()

    try:
        template_obj = _resolve_template(request.template)
        asset_order = _get_asset_order(template_obj)
        missing = [asset for asset in asset_order if asset not in request.assets]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot finalize draft. Missing assets: {', '.join(missing)}",
            )

        ordered_assets = {asset_name: request.assets[asset_name] for asset_name in asset_order}
        character_name = infer_character_display_name_from_assets(ordered_assets) or "unnamed_character"
        config = load_config()
        draft_path = create_draft_dir(
            ordered_assets,
            character_name,
            seed=request.seed,
            mode=request.mode,
            model=config.model,
            template=template_obj,
        )

        return GenerationComplete(
            draft_path=str(draft_path),
            draft_id=draft_path.name,
            character_name=character_name,
            duration_ms=(time.time() - start_time) * 1000,
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/single")
async def generate_single(request: GenerateRequest, http_request: Request):
    """Generate a single character with SSE streaming."""
    from bpui.api.byok import build_request_config

    return await _generate_single(
        seed=request.seed,
        mode=request.mode,
        request_config=build_request_config(http_request),
        template=request.template,
    )


@router.post("/batch")
async def generate_batch(request: GenerateBatchRequest, http_request: Request):
    """Generate multiple characters with SSE streaming."""
    from bpui.api.byok import build_request_config

    request_config = build_request_config(http_request)

    async def event_generator():
        max_concurrent = request.max_concurrent if request.parallel else 1
        semaphore = asyncio.Semaphore(max_concurrent)
        event_queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def generate_with_semaphore(seed: str, index: int):
            async with semaphore:
                try:
                    from bpui.llm.factory import create_engine
                    from bpui.utils.file_io.pack_io import create_draft_dir

                    await event_queue.put(
                        f"event: batch_start\ndata: {json.dumps({'index': index, 'seed': seed})}\n\n"
                    )

                    config = request_config
                    engine = create_engine(config)
                    template_obj = _resolve_template(request.template)
                    assets, character_name = await _generate_assets_sequential(
                        seed=seed,
                        mode=request.mode,
                        template_obj=template_obj,
                        engine=engine,
                    )
                    draft_path = create_draft_dir(
                        assets,
                        character_name,
                        seed=seed,
                        mode=request.mode,
                        model=config.model,
                        template=template_obj,
                    )

                    await event_queue.put(
                        f"event: batch_complete\ndata: {json.dumps({'index': index, 'seed': seed, 'draft_path': str(draft_path), 'draft_id': draft_path.name, 'character_name': character_name})}\n\n"
                    )

                except Exception as e:
                    await event_queue.put(
                        f"event: batch_error\ndata: {json.dumps({'index': index, 'seed': seed, 'error': str(e)})}\n\n"
                    )
                finally:
                    await event_queue.put(None)

        tasks = [
            asyncio.create_task(generate_with_semaphore(seed, index))
            for index, seed in enumerate(request.seeds)
        ]

        completed_tasks = 0
        while completed_tasks < len(tasks):
            event = await event_queue.get()
            if event is None:
                completed_tasks += 1
                continue
            yield event

        await asyncio.gather(*tasks)

        yield f"event: complete\ndata: {json.dumps({'total': len(request.seeds)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
