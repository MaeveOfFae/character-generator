"""Validation router."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from bpui.core.content_validation import validate_file_content
from bpui.core.parse_blocks import get_asset_filename
from bpui.utils.metadata.metadata import DraftMetadata

from ..schemas.validation import ValidatePathRequest, ValidationResponse
from ..routers.drafts import _find_draft_dir, _load_template_for_draft

router = APIRouter()


def _repo_root() -> Path:
    return Path.cwd().resolve()


def _resolve_workspace_path(path_str: str) -> Path:
    repo_root = _repo_root()
    candidate = Path(path_str).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()

    if not resolved.is_relative_to(repo_root):
        raise HTTPException(status_code=400, detail="Validation path must stay within the workspace")

    return resolved


def _run_validation(target_path: Path) -> ValidationResponse:
    from bpui.validate import validate_pack

    metadata = DraftMetadata.load(target_path)
    template = _load_template_for_draft(target_path, metadata.to_dict() if metadata else None)
    template_name = metadata.template_name if metadata else None

    if template_name and template_name != "V2/V3 Card":
        if not template:
            return ValidationResponse(
                path=str(target_path),
                output="",
                errors=f"Template not found for draft validation: {template_name}",
                exit_code=1,
                success=False,
            )

        findings: list[str] = []
        asset_paths: list[Path] = []

        for asset in template.assets:
            asset_path = target_path / get_asset_filename(asset.name, template)
            if asset.required and not asset_path.is_file():
                findings.append(f"- {asset_path}: Missing required file: {asset_path.name}")
                continue
            if asset_path.is_file():
                asset_paths.append(asset_path)

        if not findings:
            for asset_path in asset_paths:
                labels = validate_file_content(asset_path)
                for label in sorted(set(labels)):
                    findings.append(f"- {asset_path}: Found validation issue: {label}")

        if findings:
            return ValidationResponse(
                path=str(target_path),
                output="VALIDATION FAILED\n" + "\n".join(findings) + "\n",
                errors="",
                exit_code=1,
                success=False,
            )

        return ValidationResponse(
            path=str(target_path),
            output="OK\n",
            errors="",
            exit_code=0,
            success=True,
        )

    result = validate_pack(target_path, repo_root=_repo_root())
    return ValidationResponse(
        path=str(target_path),
        output=result.get("output", ""),
        errors=result.get("errors", ""),
        exit_code=result.get("exit_code", 1),
        success=result.get("success", False),
    )


@router.post("/path", response_model=ValidationResponse)
async def validate_path(request: ValidatePathRequest):
    """Validate a workspace-relative directory path."""
    target_path = _resolve_workspace_path(request.path)
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {target_path}")
    if not target_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {target_path}")
    return _run_validation(target_path)


@router.get("/draft/{draft_id}", response_model=ValidationResponse)
async def validate_draft(draft_id: str):
    """Validate a saved draft by review identifier."""
    draft_path = _find_draft_dir(draft_id)
    return _run_validation(draft_path.resolve())