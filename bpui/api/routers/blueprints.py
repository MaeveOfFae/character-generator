"""Blueprint browsing and editing router."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ..schemas.blueprints import BlueprintListSchema, BlueprintSchema, UpdateBlueprintRequest

router = APIRouter()


def _blueprints_root() -> Path:
    from bpui.features.templates.templates import OFFICIAL_BLUEPRINTS_DIR

    return OFFICIAL_BLUEPRINTS_DIR.resolve()


def _validate_relative_blueprint_path(blueprint_path: str) -> Path:
    relative_path = Path(blueprint_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HTTPException(status_code=400, detail="Invalid blueprint path")

    full_path = (_blueprints_root() / relative_path).resolve()
    root = _blueprints_root()
    if not full_path.is_file() or not str(full_path).endswith(".md"):
        raise HTTPException(status_code=404, detail=f"Blueprint not found: {blueprint_path}")
    if not full_path.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Invalid blueprint path")

    return full_path


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    pattern = r"^\s*---\s*\n(.*?)\n\s*---\s*\n?(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)
    frontmatter: dict[str, Any] = {}

    for raw_line in frontmatter_text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value.lower() in {"true", "false"}:
            frontmatter[key] = value.lower() == "true"
        else:
            frontmatter[key] = value

    return frontmatter, body


def _category_for_relative_path(relative_path: Path) -> str:
    parts = relative_path.parts
    if not parts:
        return "core"
    if parts[0] == "system":
        return "system"
    if parts[0] == "templates":
        return "template"
    if parts[0] == "examples":
        return "example"
    return "core"


def _build_blueprint_schema(full_path: Path) -> BlueprintSchema:
    root = _blueprints_root()
    relative_path = full_path.relative_to(root)
    content = full_path.read_text(encoding="utf-8")
    frontmatter, _body = _parse_frontmatter(content)

    return BlueprintSchema(
        name=str(frontmatter.get("name") or full_path.stem),
        description=str(frontmatter.get("description") or ""),
        invokable=bool(frontmatter.get("invokable", True)),
        version=str(frontmatter.get("version") or "1.0"),
        content=content,
        path=relative_path.as_posix(),
        category=_category_for_relative_path(relative_path),
    )


@router.get("", response_model=BlueprintListSchema)
async def list_blueprints() -> BlueprintListSchema:
    """List all available blueprints grouped by category."""
    root = _blueprints_root()
    if not root.exists():
        return BlueprintListSchema()

    core = [
        _build_blueprint_schema(path)
        for path in sorted(root.glob("*.md"))
        if path.name != "README.md"
    ]

    system_dir = root / "system"
    system = [
        _build_blueprint_schema(path)
        for path in sorted(system_dir.glob("*.md"))
    ] if system_dir.exists() else []

    templates: dict[str, list[BlueprintSchema]] = {}
    templates_dir = root / "templates"
    if templates_dir.exists():
        for template_dir in sorted(path for path in templates_dir.iterdir() if path.is_dir()):
            templates[template_dir.name] = [
                _build_blueprint_schema(path)
                for path in sorted(template_dir.glob("*.md"))
            ]

    examples_dir = root / "examples"
    examples = [
        _build_blueprint_schema(path)
        for path in sorted(examples_dir.glob("*.md"))
    ] if examples_dir.exists() else []

    return BlueprintListSchema(
        core=core,
        system=system,
        templates=templates,
        examples=examples,
    )


@router.get("/{blueprint_path:path}", response_model=BlueprintSchema)
async def get_blueprint(blueprint_path: str) -> BlueprintSchema:
    """Get a single blueprint by relative path."""
    full_path = _validate_relative_blueprint_path(blueprint_path)
    return _build_blueprint_schema(full_path)


@router.put("/{blueprint_path:path}", response_model=BlueprintSchema)
async def update_blueprint(blueprint_path: str, request: UpdateBlueprintRequest) -> BlueprintSchema:
    """Update an existing blueprint file."""
    full_path = _validate_relative_blueprint_path(blueprint_path)
    full_path.write_text(request.content, encoding="utf-8")
    return _build_blueprint_schema(full_path)