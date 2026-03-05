"""Centralized exception-to-HTTP mapping."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    ConflictError,
    DomainException,
    InsufficientDataError,
    ModelNotReadyError,
    NotFoundError,
    ValidationError,
    InfrastructureError,
)


def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Map domain exceptions to appropriate HTTP responses."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ModelNotReadyError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, InsufficientDataError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, InfrastructureError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
