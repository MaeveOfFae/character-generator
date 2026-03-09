"""Generation router with SSE streaming."""

import asyncio
import json
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.generation import GenerateRequest, GenerateBatchRequest

router = APIRouter()


async def _generate_single(seed: str, mode: str, template: str | None = None):
    """Generate a single character with SSE streaming."""
    start_time = time.time()

    async def event_generator():
        try:
            # Import here to avoid circular imports
            from bpui.llm.factory import create_engine
            from bpui.core.config import load_config
            from bpui.core.prompting import build_orchestrator_prompt
            from bpui.core.parse_blocks import extract_character_name, parse_blueprint_output
            from bpui.features.templates.templates import TemplateManager
            from bpui.utils.file_io.pack_io import create_draft_dir

            # Emit initializing status
            yield f"event: status\ndata: {json.dumps({'stage': 'initializing', 'status': 'started'})}\n\n"

            # Load config and create engine
            config = load_config()
            engine = create_engine(config)
            template_obj = None
            if template:
                template_obj = TemplateManager().get_template(template)
                if not template_obj:
                    raise ValueError(f"Template not found: {template}")

            # Build prompts
            yield f"event: status\ndata: {json.dumps({'stage': 'orchestrator', 'status': 'in_progress'})}\n\n"

            system_prompt, user_prompt = build_orchestrator_prompt(
                seed=seed,
                mode=mode,
                template=template_obj,
            )

            # Stream generation
            full_response = ""
            async for chunk in engine.generate_stream(system_prompt, user_prompt):
                full_response += chunk
                yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"

            # Parse assets
            yield f"event: status\ndata: {json.dumps({'stage': 'parsing', 'status': 'in_progress'})}\n\n"

            assets = parse_blueprint_output(full_response, template_obj)

            # Save draft
            yield f"event: status\ndata: {json.dumps({'stage': 'saving', 'status': 'in_progress'})}\n\n"
            character_name = extract_character_name(assets.get("character_sheet", "")) or "unnamed_character"

            draft_path = create_draft_dir(
                assets,
                character_name,
                seed=seed,
                mode=mode,
                model=config.model,
                template=template_obj,
            )

            # Complete
            duration_ms = (time.time() - start_time) * 1000
            yield f"event: status\ndata: {json.dumps({'stage': 'complete', 'status': 'complete'})}\n\n"
            yield f"event: complete\ndata: {json.dumps({'draft_path': str(draft_path), 'draft_id': draft_path.name, 'character_name': character_name, 'duration_ms': duration_ms})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/single")
async def generate_single(request: GenerateRequest):
    """Generate a single character with SSE streaming."""
    return await _generate_single(
        seed=request.seed,
        mode=request.mode,
        template=request.template,
    )


@router.post("/batch")
async def generate_batch(request: GenerateBatchRequest):
    """Generate multiple characters with SSE streaming."""
    async def event_generator():
        max_concurrent = request.max_concurrent if request.parallel else 1
        semaphore = asyncio.Semaphore(max_concurrent)
        event_queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def generate_with_semaphore(seed: str, index: int):
            async with semaphore:
                try:
                    from bpui.llm.factory import create_engine
                    from bpui.core.config import load_config
                    from bpui.core.prompting import build_orchestrator_prompt
                    from bpui.core.parse_blocks import extract_character_name, parse_blueprint_output
                    from bpui.features.templates.templates import TemplateManager
                    from bpui.utils.file_io.pack_io import create_draft_dir

                    await event_queue.put(
                        f"event: batch_start\ndata: {json.dumps({'index': index, 'seed': seed})}\n\n"
                    )

                    config = load_config()
                    engine = create_engine(config)
                    template_obj = None
                    if request.template:
                        template_obj = TemplateManager().get_template(request.template)
                        if not template_obj:
                            raise ValueError(f"Template not found: {request.template}")

                    system_prompt, user_prompt = build_orchestrator_prompt(seed, request.mode, template=template_obj)

                    full_response = ""
                    async for chunk in engine.generate_stream(system_prompt, user_prompt):
                        full_response += chunk

                    assets = parse_blueprint_output(full_response, template_obj)
                    character_name = extract_character_name(assets.get("character_sheet", "")) or "unnamed_character"
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
