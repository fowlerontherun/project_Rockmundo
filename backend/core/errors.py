from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationErrorItem(BaseModel):
    loc: List[str] = Field(..., description="Location of the error (e.g., ['body', 'field']).")
    msg: str = Field(..., description="Human-friendly error message.")
    type: str = Field(..., description="Error type code (e.g., 'value_error').")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Stable error code (snake_case).")
    message: str = Field(..., description="Human-friendly error message.")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra metadata.")
    request_id: Optional[str] = Field(default=None, description="Request correlation ID for support.")
    validation: Optional[List[ValidationErrorItem]] = Field(
        default=None, description="Validation error details when applicable."
    )
