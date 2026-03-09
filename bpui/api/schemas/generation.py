"""Generation-related schemas."""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from .config import ContentMode


class GenerateRequest(BaseModel):
    """Request to generate a character."""
    seed: str = Field(..., min_length=1, max_length=2000)
    template: Optional[str] = None
    mode: ContentMode = "SFW"
    stream: bool = True


class GenerateBatchRequest(BaseModel):
    """Request to generate multiple characters."""
    seeds: List[str] = Field(..., min_length=1, max_length=100)
    template: Optional[str] = None
    mode: ContentMode = "SFW"
    parallel: bool = True
    max_concurrent: int = Field(default=3, ge=1, le=10)


class OffspringRequest(BaseModel):
    """Request to generate an offspring character from two parents."""
    parent1_id: str = Field(..., min_length=1)
    parent2_id: str = Field(..., min_length=1)
    mode: ContentMode = "SFW"
    template: Optional[str] = None
    seed: Optional[str] = None


class GenerationProgress(BaseModel):
    """Progress update during generation."""
    stage: Literal["initializing", "orchestrator", "parsing", "saving", "complete", "error"]
    status: Literal["started", "in_progress", "complete", "error"]
    asset: Optional[str] = None
    content: Optional[str] = None
    progress: Optional[float] = None
    error: Optional[str] = None


class GenerationComplete(BaseModel):
    """Final completion message."""
    draft_path: str
    draft_id: Optional[str] = None
    character_name: Optional[str] = None
    duration_ms: float
