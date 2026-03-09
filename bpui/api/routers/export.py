"""Export router."""

import io
import json
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from bpui.utils.file_io.pack_io import load_draft

from ..routers.drafts import _find_draft_dir, _load_template_for_draft
from ..schemas.export import ExportRequest, ExportResponse, ExportPresetSchema, FieldMappingSchema

router = APIRouter()


def _resolve_export_entry_name(target: str) -> str:
    """Resolve an exported file name without duplicating existing extensions."""
    if Path(target).suffix:
        return target

    if target == "intro_page" or "page" in target:
        return f"{target}.md"

    return f"{target}.txt"


def _iter_exportable_draft_files(draft_path: Path) -> list[Path]:
    """Return top-level text/markdown asset files from a draft directory."""
    return sorted(
        path
        for path in draft_path.iterdir()
        if path.is_file() and path.suffix in {".txt", ".md"} and not path.name.startswith(".")
    )

def _load_assets(draft_path: Path) -> dict[str, str]:
    """Load all assets from a draft directory."""
    template = _load_template_for_draft(draft_path)
    return load_draft(draft_path, template)


def _load_metadata(draft_path: Path) -> dict:
    """Load metadata from a draft directory."""
    metadata_file = draft_path / ".metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


@router.get("/presets")
async def list_presets():
    """List available export presets."""
    try:
        from bpui.features.export.export_presets import list_presets as _list_presets, load_preset

        presets_dir = Path("presets")
        preset_list = _list_presets(presets_dir)

        return {
            "presets": [
                {
                    "name": name,
                    "path": str(path),
                    "format": preset.format if preset else "text",
                    "description": preset.description if preset else "",
                }
                for name, path in preset_list
                for preset in [load_preset(path)]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_preset(requested_preset: str):
    from bpui.features.export.export_presets import load_preset, resolve_preset_path

    preset_path = resolve_preset_path(requested_preset, Path("presets"))
    if not preset_path:
        raise HTTPException(status_code=404, detail=f"Preset not found: {requested_preset}")

    preset = load_preset(preset_path)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {requested_preset}")

    return preset_path, preset


@router.get("/presets/{preset_name}")
async def get_preset(preset_name: str):
    """Get details of a specific preset."""
    try:
        _, preset = _resolve_preset(preset_name)

        return ExportPresetSchema(
            name=preset.name,
            format=preset.format,
            description=preset.description,
            fields=[
                FieldMappingSchema(
                    asset=f.asset,
                    target=f.target,
                    wrapper=f.wrapper,
                    optional=f.optional,
                )
                for f in preset.fields
            ],
            metadata=preset.metadata,
            output_pattern=preset.output_pattern,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def export_draft(request: ExportRequest):
    """Export a draft using a preset."""
    try:
        from bpui.features.export.export_presets import apply_preset

        # Find draft
        draft_path = _find_draft_dir(request.draft_id)

        # Load assets and metadata
        assets = _load_assets(draft_path)
        metadata = _load_metadata(draft_path)
        character_name = metadata.get("character_name", draft_path.name)

        # Load preset
        preset_path, preset = _resolve_preset(request.preset)

        if preset_path.stem == "raw":
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in _iter_exportable_draft_files(draft_path):
                    zf.writestr(file_path.name, file_path.read_text(encoding='utf-8'))

                if request.include_metadata:
                    zf.writestr(
                        "_metadata.json",
                        json.dumps(
                            {
                                "source_path": str(draft_path),
                                "exported_at": metadata.get("modified") or metadata.get("created"),
                                "template": metadata.get("template_name"),
                                "mode": metadata.get("mode"),
                            },
                            indent=2,
                        ),
                    )

            zip_buffer.seek(0)
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{character_name}.zip"'
                }
            )

        # Apply preset
        export_data = apply_preset(assets, preset, character_name)

        if request.include_metadata:
            export_data["_metadata"] = {
                "source_path": str(draft_path),
                "exported_at": metadata.get("modified") or metadata.get("created"),
                "template": metadata.get("template_name"),
                "mode": metadata.get("mode"),
            }

        # Return based on format
        if preset.format == "json":
            return JSONResponse(
                content=export_data,
                headers={
                    "Content-Disposition": f'attachment; filename="{character_name}.json"'
                }
            )

        elif preset.format == "combined":
            # Create combined text
            output = io.StringIO()
            for key, value in export_data.items():
                if key == "_metadata":
                    continue
                output.write(f"=== {key.upper()} ===\n\n")
                output.write(str(value))
                output.write("\n\n")

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/plain",
                headers={
                    "Content-Disposition": f'attachment; filename="{character_name}.txt"'
                }
            )

        else:  # text format - return as zip
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for key, value in export_data.items():
                    if key == "_metadata":
                        continue
                    zf.writestr(_resolve_export_entry_name(key), str(value))

                if request.include_metadata and "_metadata" in export_data:
                    zf.writestr("_metadata.json", json.dumps(export_data["_metadata"], indent=2))

            zip_buffer.seek(0)
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{character_name}.zip"'
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_export(request: ExportRequest):
    """Preview export output without downloading."""
    try:
        from bpui.features.export.export_presets import apply_preset

        # Find draft
        draft_path = _find_draft_dir(request.draft_id)

        # Load assets and metadata
        assets = _load_assets(draft_path)
        metadata = _load_metadata(draft_path)
        character_name = metadata.get("character_name", draft_path.name)

        # Load preset
        _, preset = _resolve_preset(request.preset)

        # Apply preset
        export_data = apply_preset(assets, preset, character_name)

        return {
            "character_name": character_name,
            "format": preset.format,
            "fields": list(export_data.keys()),
            "preview": {
                k: v[:200] + "..." if len(str(v)) > 200 else v
                for k, v in list(export_data.items())[:5]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
