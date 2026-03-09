"""Seed generator schemas."""

from pydantic import BaseModel, Field


class SeedGenerationRequest(BaseModel):
    """Request to generate character seeds."""

    genre_lines: str = ""
    surprise_mode: bool = False


class SeedGenerationResponse(BaseModel):
    """Generated seed list."""

    seeds: list[str] = Field(default_factory=list)
