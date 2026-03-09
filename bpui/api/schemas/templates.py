"""Template-related schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class AssetDefinitionSchema(BaseModel):
    """Definition of a template asset."""
    name: str
    required: bool = True
    depends_on: List[str] = Field(default_factory=list)
    description: str = ""
    blueprint_file: Optional[str] = None

    class Config:
        from_attributes = True


class TemplateSchema(BaseModel):
    """A character generation template."""
    name: str
    version: str = "1.0"
    description: str = ""
    assets: List[AssetDefinitionSchema] = Field(default_factory=list)
    is_official: bool = False
    path: Optional[str] = None

    class Config:
        from_attributes = True


class CreateTemplateRequest(BaseModel):
    """Request to create a new template."""
    name: str = Field(..., min_length=1, max_length=100)
    version: str = "1.0"
    description: str = ""
    assets: List[AssetDefinitionSchema] = Field(default_factory=list)
    blueprint_contents: dict[str, str] = Field(default_factory=dict)


class DuplicateTemplateRequest(BaseModel):
    """Request to duplicate a template."""

    name: str = Field(..., min_length=1, max_length=100)
    version: str = "1.0"


class TemplateValidationResult(BaseModel):
    """Validation result for a template."""

    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TemplateBlueprintContentsResponse(BaseModel):
    """Blueprint content mapped by asset name for a template."""

    blueprint_contents: dict[str, str] = Field(default_factory=dict)
