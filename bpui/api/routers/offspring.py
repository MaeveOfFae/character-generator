"""Offspring generation router."""

import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.generation import OffspringRequest
from .drafts import _find_draft_dir

router = APIRouter()


@router.post("")
async def generate_offspring(request: OffspringRequest):
    """Generate offspring character from two parents with SSE streaming."""
    async def event_generator():
        try:
            from bpui.core.config import load_config
            from bpui.llm.factory import create_engine
            from bpui.core.prompting import build_offspring_prompt, build_asset_prompt
            from bpui.core.parse_blocks import extract_single_asset, extract_character_name
            from bpui.utils.file_io.pack_io import load_draft, create_draft_dir
            from bpui.utils.topological_sort import topological_sort
            from bpui.features.templates.templates import TemplateManager

            yield f"event: status\ndata: {json.dumps({'stage': 'initializing', 'status': 'started'})}\n\n"

            # Load parents
            parent1_path = _find_draft_dir(request.parent1_id)
            parent2_path = _find_draft_dir(request.parent2_id)

            parent1_assets = load_draft(parent1_path)
            parent2_assets = load_draft(parent2_path)

            # Get parent names
            parent1_name = parent1_path.name
            parent2_name = parent2_path.name

            # Extract names from character sheets
            for line in (parent1_assets.get("character_sheet") or "").split("\n")[:10]:
                if line.strip().lower().startswith("name:"):
                    parent1_name = line.split(":", 1)[1].strip()
                    break
            for line in (parent2_assets.get("character_sheet") or "").split("\n")[:10]:
                if line.strip().lower().startswith("name:"):
                    parent2_name = line.split(":", 1)[1].strip()
                    break

            yield f"event: status\ndata: {json.dumps({'stage': 'parents_loaded', 'parent1': parent1_name, 'parent2': parent2_name})}\n\n"

            # Load config and create engine
            config = load_config()
            engine = create_engine(config)

            # Get template
            template_manager = TemplateManager()
            template_obj = template_manager.get_template(request.template or "Official RPBotGenerator")
            if not template_obj:
                raise ValueError(f"Template not found: {request.template}")

            # Step 1: Generate offspring seed
            yield f"event: status\ndata: {json.dumps({'stage': 'seed_generation', 'status': 'in_progress'})}\n\n"

            if request.seed:
                offspring_seed = request.seed
            else:
                system_prompt, user_prompt = build_offspring_prompt(
                    parent1_assets=parent1_assets,
                    parent2_assets=parent2_assets,
                    parent1_name=parent1_name,
                    parent2_name=parent2_name,
                    mode=request.mode,
                )
                offspring_seed = await engine.generate(system_prompt, user_prompt)
                offspring_seed = offspring_seed.strip()

            yield f"event: status\ndata: {json.dumps({'stage': 'seed_generation', 'status': 'complete', 'seed_preview': offspring_seed[:100]})}\n\n"

            # Step 2: Generate assets
            yield f"event: status\ndata: {json.dumps({'stage': 'asset_generation', 'status': 'in_progress'})}\n\n"

            asset_order = topological_sort(template_obj.assets)
            assets = {}
            character_name = None

            for i, asset_name in enumerate(asset_order):
                yield f"event: asset\ndata: {json.dumps({'name': asset_name, 'status': 'started', 'progress': i / len(asset_order)})}\n\n"

                system_prompt, user_prompt = build_asset_prompt(
                    asset_name, offspring_seed, request.mode, assets
                )

                output = await engine.generate(system_prompt, user_prompt)
                asset_content = extract_single_asset(output, asset_name)
                assets[asset_name] = asset_content

                if asset_name == "character_sheet" and not character_name:
                    character_name = extract_character_name(asset_content)

                yield f"event: asset_complete\ndata: {json.dumps({'name': asset_name, 'length': len(asset_content)})}\n\n"

            if not character_name:
                character_name = "offspring_character"

            # Step 3: Save draft with lineage
            yield f"event: status\ndata: {json.dumps({'stage': 'saving', 'status': 'in_progress'})}\n\n"

            drafts_root = Path("drafts").resolve()
            parent1_rel = str(parent1_path.relative_to(drafts_root)) if parent1_path.is_relative_to(drafts_root) else parent1_path.name
            parent2_rel = str(parent2_path.relative_to(drafts_root)) if parent2_path.is_relative_to(drafts_root) else parent2_path.name

            draft_path = create_draft_dir(
                assets,
                character_name,
                seed=offspring_seed[:200],
                mode=request.mode,
                model=config.model,
                template=template_obj,
            )

            metadata_path = draft_path / ".metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            metadata.update(
                {
                    "template_name": template_obj.name,
                    "character_name": character_name,
                    "parent_drafts": [parent1_rel, parent2_rel],
                    "offspring_type": "generated",
                }
            )

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            yield f"event: status\ndata: {json.dumps({'stage': 'complete', 'status': 'complete'})}\n\n"
            yield f"event: complete\ndata: {json.dumps({'draft_path': str(draft_path), 'draft_id': draft_path.name, 'character_name': character_name, 'parents': [parent1_name, parent2_name]})}\n\n"

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
