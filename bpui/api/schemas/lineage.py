"""Lineage-related schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LineageNodeSchema(BaseModel):
    """Serialized lineage node for API responses."""

    id: str
    review_id: str
    draft_name: str
    character_name: str
    generation: int
    is_root: bool
    is_leaf: bool
    offspring_type: Optional[str] = None
    mode: Optional[str] = None
    model: Optional[str] = None
    created: Optional[str] = None
    parent_ids: list[str] = Field(default_factory=list)
    child_ids: list[str] = Field(default_factory=list)
    parent_names: list[str] = Field(default_factory=list)
    child_names: list[str] = Field(default_factory=list)
    sibling_names: list[str] = Field(default_factory=list)
    num_ancestors: int = 0
    num_descendants: int = 0


class LineageStatsSchema(BaseModel):
    """Lineage tree statistics."""

    total_characters: int = 0
    root_characters: int = 0
    leaf_characters: int = 0
    generations: int = 0


class LineageResponse(BaseModel):
    """Full lineage graph response."""

    nodes: list[LineageNodeSchema] = Field(default_factory=list)
    roots: list[str] = Field(default_factory=list)
    max_generation: int = 0
    stats: LineageStatsSchema = Field(default_factory=LineageStatsSchema)