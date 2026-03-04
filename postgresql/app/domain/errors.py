from __future__ import annotations


class ServiceError(Exception):
    """Base service error."""


class DatabaseUnavailableError(ServiceError):
    """Database is unavailable."""

