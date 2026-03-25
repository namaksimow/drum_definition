from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend_app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DataIntegrityError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from backend_app.presentation.http.error_mapper import to_http_exception


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (ValidationError("bad input"), 400),
        (AuthenticationError("bad auth"), 401),
        (ForbiddenError("forbidden"), 403),
        (NotFoundError("missing"), 404),
        (ConflictError("conflict"), 409),
        (ExternalServiceError("gateway"), 502),
        (DataIntegrityError("broken"), 500),
    ],
)
def test_to_http_exception_maps_domain_errors(exc: Exception, status: int) -> None:
    mapped = to_http_exception(exc)
    assert isinstance(mapped, HTTPException)
    assert mapped.status_code == status


def test_to_http_exception_maps_unknown_error_to_generic_500() -> None:
    mapped = to_http_exception(RuntimeError("unknown"))
    assert mapped.status_code == 500
    assert mapped.detail == "Unexpected backend error"

