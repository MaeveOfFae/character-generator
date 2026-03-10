"""Chat/refinement router."""

import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from . import drafts as drafts_router

router = APIRouter()


class ChatMessage(BaseModel):
    """A chat message."""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """Request for chat-based refinement."""
    draft_id: Optional[str] = None
    messages: List[ChatMessage]
    context_asset: Optional[str] = None  # Asset to use as context
    screen_context: Optional[dict] = None


class RefineRequest(BaseModel):
    """Request to refine a specific asset."""
    draft_id: str
    asset: str
    message: str  # User's refinement request


@router.post("")
async def chat(request: ChatRequest, http_request: Request):
    """Chat-based refinement with SSE streaming."""
    async def event_generator():
        try:
            from bpui.api.byok import build_request_config
            from bpui.llm.factory import create_engine

            # Build context
            context_parts = ["You are helping with the Character Generator workflow."]

            if request.screen_context:
                screen_name = request.screen_context.get("screen_name") or "unknown"
                screen_title = request.screen_context.get("screen_title") or screen_name
                context_parts.append(f"\nCurrent screen: {screen_title} ({screen_name})")
                context_parts.append("\nScreen context:")
                for key, value in request.screen_context.items():
                    if key in {"screen_name", "screen_title"}:
                        continue
                    context_parts.append(f"- {key}: {value}")

            if request.draft_id:
                draft_path = drafts_router._find_draft_dir(request.draft_id)
                assets = drafts_router._load_assets(draft_path)
                context_parts.append("\n\nCurrent character data:\n")

                if request.context_asset and request.context_asset in assets:
                    context_parts.append(f"\n=== {request.context_asset.upper()} ===\n")
                    context_parts.append(assets[request.context_asset])
                else:
                    for asset_name, content in assets.items():
                        context_parts.append(f"\n=== {asset_name.upper()} ===\n")
                        context_parts.append(content[:1000])

            system_prompt = "".join(context_parts)
            system_prompt += "\n\nHelp the user refine or navigate the workflow. Be concrete, brief, and useful."

            # Create engine
            config = build_request_config(http_request)
            engine = create_engine(config)

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend({"role": m.role, "content": m.content} for m in request.messages)

            # Stream response
            full_response = ""
            async for chunk in engine.generate_chat_stream(messages):
                full_response += chunk
                yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'length': len(full_response)})}\n\n"

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


@router.post("/refine")
async def refine_asset(request: RefineRequest, http_request: Request):
    """Refine a specific asset with SSE streaming."""
    async def event_generator():
        try:
            from bpui.api.byok import build_request_config
            from bpui.llm.factory import create_engine

            # Find draft and load assets
            draft_path = drafts_router._find_draft_dir(request.draft_id)
            assets = drafts_router._load_assets(draft_path)

            if request.asset not in assets:
                raise ValueError(f"Asset not found: {request.asset}")

            current_content = assets[request.asset]

            # Build refinement prompt
            system_prompt = f"""You are helping refine a character asset.

Current {request.asset}:
---
{current_content}
---

User request: {request.message}

Please provide an updated version of the {request.asset} that addresses the user's request.
Only output the updated content, no explanations or markdown."""

            # Create engine
            config = build_request_config(http_request)
            engine = create_engine(config)

            # Stream response
            full_response = ""
            async for chunk in engine.generate_stream(system_prompt, ""):
                full_response += chunk
                yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"

            yield f"event: complete\ndata: {json.dumps({'asset': request.asset, 'length': len(full_response)})}\n\n"

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


@router.post("/apply-refinement")
async def apply_refinement(draft_id: str, asset: str, content: str):
    """Apply refined content to an asset."""
    try:
        draft_path = drafts_router._find_draft_dir(draft_id)
        metadata = drafts_router._load_metadata(draft_path)
        asset_file = drafts_router._resolve_asset_path(draft_path, asset, metadata)

        if not asset_file.exists():
            raise HTTPException(status_code=404, detail=f"Asset file not found: {asset}")

        # Write new content
        with open(asset_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Update metadata modified timestamp
        import json
        from datetime import datetime
        metadata_file = draft_path / ".metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata["modified"] = datetime.now().isoformat()
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

        return {"status": "updated", "asset": asset, "length": len(content)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
