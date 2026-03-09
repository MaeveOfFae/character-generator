"""Templates router."""

import io
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from ..schemas.templates import (
    TemplateSchema,
    AssetDefinitionSchema,
    CreateTemplateRequest,
    DuplicateTemplateRequest,
    TemplateBlueprintContentsResponse,
    TemplateValidationResult,
)

router = APIRouter()


@router.get("", response_model=List[TemplateSchema])
async def list_templates():
    """List all available templates."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        templates = manager.list_templates()

        return [
            TemplateSchema(
                name=t.name,
                version=t.version,
                description=t.description,
                assets=[
                    AssetDefinitionSchema(
                        name=a.name,
                        required=a.required,
                        depends_on=a.depends_on,
                        description=a.description,
                        blueprint_file=a.blueprint_file,
                    )
                    for a in t.assets
                ],
                is_official=t.is_official,
                path=str(t.path) if t.path else None,
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=TemplateSchema)
async def get_template(name: str):
    """Get a specific template by name."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        template = manager.get_template(name)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        return TemplateSchema(
            name=template.name,
            version=template.version,
            description=template.description,
            assets=[
                AssetDefinitionSchema(
                    name=a.name,
                    required=a.required,
                    depends_on=a.depends_on,
                    description=a.description,
                    blueprint_file=a.blueprint_file,
                )
                for a in template.assets
            ],
            is_official=template.is_official,
            path=str(template.path) if template.path else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=TemplateSchema)
async def create_template(request: CreateTemplateRequest):
    """Create a new custom template."""
    try:
        from bpui.features.templates.templates import TemplateManager, Template, AssetDefinition

        manager = TemplateManager()

        # Convert request to internal format
        assets = [
            AssetDefinition(
                name=a.name,
                required=a.required,
                depends_on=a.depends_on,
                description=a.description,
                blueprint_file=a.blueprint_file,
            )
            for a in request.assets
        ]

        created = manager.create_template(
            name=request.name,
            description=request.description,
            assets=assets,
            version=request.version,
            blueprint_contents=request.blueprint_contents,
        )

        return TemplateSchema(
            name=created.name,
            version=created.version,
            description=created.description,
            assets=[
                AssetDefinitionSchema(
                    name=a.name,
                    required=a.required,
                    depends_on=a.depends_on,
                    description=a.description,
                    blueprint_file=a.blueprint_file,
                )
                for a in created.assets
            ],
            is_official=False,
            path=str(created.path) if created.path else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}", response_model=TemplateSchema)
async def update_template(name: str, request: CreateTemplateRequest):
    """Update a custom template."""
    try:
        from bpui.features.templates.templates import TemplateManager, AssetDefinition

        manager = TemplateManager()
        assets = [
            AssetDefinition(
                name=a.name,
                required=a.required,
                depends_on=a.depends_on,
                description=a.description,
                blueprint_file=a.blueprint_file,
            )
            for a in request.assets
        ]

        updated = manager.update_template(
            existing_name=name,
            name=request.name,
            version=request.version,
            description=request.description,
            assets=assets,
            blueprint_contents=request.blueprint_contents,
        )

        return TemplateSchema(
            name=updated.name,
            version=updated.version,
            description=updated.description,
            assets=[
                AssetDefinitionSchema(
                    name=a.name,
                    required=a.required,
                    depends_on=a.depends_on,
                    description=a.description,
                    blueprint_file=a.blueprint_file,
                )
                for a in updated.assets
            ],
            is_official=updated.is_official,
            path=str(updated.path) if updated.path else None,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/validate", response_model=TemplateValidationResult)
async def validate_template(name: str):
    """Validate a template and return errors/warnings."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        template = manager.get_template(name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        result = manager.validate_template(template)
        return TemplateValidationResult(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/blueprint-contents", response_model=TemplateBlueprintContentsResponse)
async def get_template_blueprint_contents(name: str):
    """Get blueprint contents for all template assets."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        template = manager.get_template(name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        return TemplateBlueprintContentsResponse(
            blueprint_contents=manager.get_template_blueprint_contents(template)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/duplicate", response_model=TemplateSchema)
async def duplicate_template(name: str, request: DuplicateTemplateRequest):
    """Duplicate a template under a new name."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        template = manager.get_template(name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        duplicated = manager.duplicate_template(template, request.name, version=request.version)

        return TemplateSchema(
            name=duplicated.name,
            version=duplicated.version,
            description=duplicated.description,
            assets=[
                AssetDefinitionSchema(
                    name=a.name,
                    required=a.required,
                    depends_on=a.depends_on,
                    description=a.description,
                    blueprint_file=a.blueprint_file,
                )
                for a in duplicated.assets
            ],
            is_official=duplicated.is_official,
            path=str(duplicated.path) if duplicated.path else None,
        )
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/export")
async def export_template(name: str):
    """Export a template as a zip archive."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        template = manager.get_template(name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in template.path.rglob("*"):
                if path.is_file():
                    zf.write(path, arcname=str(path.relative_to(template.path)))

        zip_buffer.seek(0)
        safe_name = template.name.lower().replace(" ", "_")
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.zip"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=TemplateSchema)
async def import_template(file: UploadFile = File(...)):
    """Import a template from a zip archive."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Template import requires a .zip archive")

    temp_dir = tempfile.mkdtemp(prefix="template-import-")
    try:
        archive_path = Path(temp_dir) / file.filename
        with open(archive_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)

        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()
        imported = manager.import_template_archive(archive_path)
        if not imported:
            raise HTTPException(status_code=400, detail="Failed to import template archive")

        return TemplateSchema(
            name=imported.name,
            version=imported.version,
            description=imported.description,
            assets=[
                AssetDefinitionSchema(
                    name=a.name,
                    required=a.required,
                    depends_on=a.depends_on,
                    description=a.description,
                    blueprint_file=a.blueprint_file,
                )
                for a in imported.assets
            ],
            is_official=imported.is_official,
            path=str(imported.path) if imported.path else None,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.delete("/{name}")
async def delete_template(name: str):
    """Delete a custom template."""
    try:
        from bpui.features.templates.templates import TemplateManager

        manager = TemplateManager()

        # Check if it's an official template
        template = manager.get_template(name)
        if template and template.is_official:
            raise HTTPException(status_code=400, detail="Cannot delete official templates")

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {name}")

        deleted = manager.delete_template(template)
        if not deleted:
            raise HTTPException(status_code=400, detail=f"Could not delete template: {name}")
        return {"status": "deleted", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
