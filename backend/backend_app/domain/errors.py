from __future__ import annotations


class BackendError(Exception):
    """Base backend domain error."""


class ValidationError(BackendError):
    """Validation failed."""


class AuthenticationError(BackendError):
    """Authentication failed."""


class ForbiddenError(BackendError):
    """Access is denied for current user role."""


class NotFoundError(BackendError):
    """Entity or file was not found."""


class ConflictError(BackendError):
    """Entity exists but is not in required state."""


class ExternalServiceError(BackendError):
    """External dependency returned an error."""


class DataIntegrityError(BackendError):
    """Required data is missing or inconsistent."""
