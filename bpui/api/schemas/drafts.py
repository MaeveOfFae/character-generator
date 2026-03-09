"""Draft-related schemas."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from .config import ContentMode


class DraftMetadataSchema(BaseModel):
    """Metadata for a character draft."""
    review_id: str
    seed: str
    mode: Optional[ContentMode] = None
    model: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    tags: Optional[List[str]] = None
    genre: Optional[str] = None
    notes: Optional[str] = None
    favorite: bool = False
    character_name: Optional[str] = None
    template_name: Optional[str] = None
    parent_drafts: Optional[List[str]] = None
    offspring_type: Optional[str] = None

    class Config:
        from_attributes = True


class DraftDetailResponse(BaseModel):
    """Full draft with assets."""
    metadata: DraftMetadataSchema
    assets: Dict[str, str]
    path: str


class DraftListResponse(BaseModel):
    """Response for listing drafts."""
    drafts: List[DraftMetadataSchema]
    total: int
    stats: Dict[str, Any]


class DraftFilters(BaseModel):
    """Filters for draft listing."""
    search: Optional[str] = None
    tags: Optional[List[str]] = None
    genre: Optional[str] = None
    mode: Optional[ContentMode] = None
    favorite: Optional[bool] = None
    sort_by: Optional[Literal["created", "modified", "name"]] = "created"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: Optional[int] = Field(default=50, ge=1, le=500)
    offset: Optional[int] = Field(default=0, ge=0)


class DraftUpdate(BaseModel):
    """Request to update a draft."""
    metadata: Optional[Dict[str, Any]] = None
    assets: Optional[Dict[str, str]] = None


class AssetUpdate(BaseModel):
    """Request to update a single asset."""
    content: str
