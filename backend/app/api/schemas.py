"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# Auth schemas
class LoginRequest(BaseModel):
    """Login request."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserResponse(BaseModel):
    """User response."""

    id: int
    email: str
    pseudonym_id: str
    is_admin: int
    created_at: datetime

    class Config:
        from_attributes = True


# Chat schemas
class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., min_length=1, max_length=5000)


class Citation(BaseModel):
    """Citation information."""

    source_number: int
    document_title: str
    section: str
    snippet: str


class ChatResponse(BaseModel):
    """Chat response."""

    answer: str
    citations: list[Citation]
    safety_outcome: str
    safety_reason: str


# Document schemas
class DocumentUploadRequest(BaseModel):
    """Document upload request (for JSON)."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source_type: str = Field(..., pattern="^(markdown|text|pdf)$")
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    """Document response."""

    id: int
    title: str
    source_type: str
    metadata: dict[str, Any] = Field(validation_alias="document_metadata")
    created_at: datetime
    updated_at: datetime
    num_chunks: int | None = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents."""

    documents: list[DocumentResponse]
    total: int


class ReindexRequest(BaseModel):
    """Reindex request."""

    document_id: int


class ReindexResponse(BaseModel):
    """Reindex response."""

    success: bool
    message: str
    document_id: int


# Generic responses
class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    details: dict[str, Any] | None = None
