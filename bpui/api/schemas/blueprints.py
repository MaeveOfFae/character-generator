"""Blueprint-related schemas."""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field


BlueprintCategory = Literal["core", "system", "template", "example"]


class BlueprintSchema(BaseModel):
    """A blueprint markdown file with parsed metadata."""

    name: str
    description: str = ""
    invokable: bool = True
    version: str = "1.0"
    content: str
    path: str
    category: BlueprintCategory


class BlueprintListSchema(BaseModel):
    """Categorized blueprint listing."""

    core: List[BlueprintSchema] = Field(default_factory=list)
    system: List[BlueprintSchema] = Field(default_factory=list)
    templates: Dict[str, List[BlueprintSchema]] = Field(default_factory=dict)
    examples: List[BlueprintSchema] = Field(default_factory=list)


class UpdateBlueprintRequest(BaseModel):
    """Update request for a blueprint markdown file."""

    content: str