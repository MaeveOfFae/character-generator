"""Validation-related schemas."""

from pydantic import BaseModel, Field


class ValidatePathRequest(BaseModel):
    """Request to validate a directory path."""

    path: str = Field(..., min_length=1)


class ValidationResponse(BaseModel):
    """Validation result."""

    path: str
    output: str = ""
    errors: str = ""
    exit_code: int = 1
    success: bool = False
