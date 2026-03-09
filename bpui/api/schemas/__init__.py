"""Pydantic schemas for the Character Generator API."""

from .config import ConfigResponse, ConfigUpdate, ConnectionTestRequest, ConnectionTestResult
from .drafts import (
    DraftMetadataSchema,
    DraftDetailResponse,
    DraftListResponse,
    DraftFilters,
    DraftUpdate,
)
from .generation import (
    GenerateRequest,
    GenerateBatchRequest,
    GenerationProgress,
    GenerationComplete,
)
from .templates import (
    TemplateSchema,
    AssetDefinitionSchema,
    CreateTemplateRequest,
    DuplicateTemplateRequest,
    TemplateValidationResult,
)

__all__ = [
    # Config
    "ConfigResponse",
    "ConfigUpdate",
    "ConnectionTestRequest",
    "ConnectionTestResult",
    # Drafts
    "DraftMetadataSchema",
    "DraftDetailResponse",
    "DraftListResponse",
    "DraftFilters",
    "DraftUpdate",
    # Generation
    "GenerateRequest",
    "GenerateBatchRequest",
    "GenerationProgress",
    "GenerationComplete",
    # Templates
    "TemplateSchema",
    "AssetDefinitionSchema",
    "CreateTemplateRequest",
    "DuplicateTemplateRequest",
    "TemplateValidationResult",
]
