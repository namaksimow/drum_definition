from __future__ import annotations

from fastapi import HTTPException

from backend_app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DataIntegrityError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


def to_http_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ExternalServiceError):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, DataIntegrityError):
        return HTTPException(status_code=500, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected backend error")
