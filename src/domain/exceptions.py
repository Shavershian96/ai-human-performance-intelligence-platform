"""Domain and application exception hierarchy.

Production-grade error handling:
- Structured exception types for proper HTTP mapping
- Error codes for client handling
- No sensitive data in messages
"""

from typing import Any, Optional


class DomainException(Exception):
    """Base exception for all domain/application errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationError(DomainException):
    """Invalid input data."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class NotFoundError(DomainException):
    """Resource not found."""

    def __init__(self, message: str, resource: Optional[str] = None):
        details = {"resource": resource} if resource else None
        super().__init__(message, code="NOT_FOUND", details=details or {})


class ModelNotReadyError(DomainException):
    """ML model not loaded or not trained."""

    def __init__(self, message: str = "Model not ready for predictions"):
        super().__init__(message, code="MODEL_NOT_READY")


class InsufficientDataError(DomainException):
    """Insufficient data for operation (e.g. training)."""

    def __init__(self, message: str, required: Optional[int] = None, actual: Optional[int] = None):
        details = {}
        if required is not None:
            details["required"] = required
        if actual is not None:
            details["actual"] = actual
        super().__init__(message, code="INSUFFICIENT_DATA", details=details)


class InfrastructureError(DomainException):
    """Database or external service failure."""

    def __init__(self, message: str, service: Optional[str] = None):
        details = {"service": service} if service else None
        super().__init__(message, code="INFRASTRUCTURE_ERROR", details=details or {})


class ConflictError(DomainException):
    """Resource conflict (e.g. duplicate)."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT")
