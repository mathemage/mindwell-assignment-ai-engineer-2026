"""Custom exceptions for the application."""

from typing import Any


class MindwellError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(MindwellError):
    """Raised when there's a configuration issue."""

    pass


class DatabaseError(MindwellError):
    """Raised when there's a database error."""

    pass


class AuthenticationError(MindwellError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(MindwellError):
    """Raised when authorization fails."""

    pass


class ValidationError(MindwellError):
    """Raised when validation fails."""

    pass


class LLMError(MindwellError):
    """Raised when LLM operations fail."""

    pass


class RAGError(MindwellError):
    """Raised when RAG operations fail."""

    pass


class SafetyError(MindwellError):
    """Raised when safety checks fail."""

    pass


class DocumentProcessingError(MindwellError):
    """Raised when document processing fails."""

    pass


class EmbeddingError(MindwellError):
    """Raised when embedding generation fails."""

    pass


class RetrievalError(MindwellError):
    """Raised when retrieval fails."""

    pass
