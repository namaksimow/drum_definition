from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import (
    AuthenticationError,
    DataIntegrityError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


class CreatePublicTablatureCommentUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, tablature_id: int, content: str) -> dict:
        status_code, payload = await self.postgres_service.create_public_tablature_comment(
            token=token,
            tablature_id=tablature_id,
            content=content,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 404:
            raise NotFoundError("Public tablature not found")
        if status_code == 400:
            raise ValidationError("Invalid comment payload")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        comment = payload.get("comment")
        if not isinstance(comment, dict):
            raise DataIntegrityError("Comment payload missing")
        return comment
