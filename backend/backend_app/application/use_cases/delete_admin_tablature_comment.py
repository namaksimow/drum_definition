from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError, NotFoundError


class DeleteAdminTablatureCommentUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, tablature_id: int, comment_id: int) -> bool:
        status_code, payload = await self.postgres_service.delete_admin_tablature_comment(
            token=token,
            tablature_id=tablature_id,
            comment_id=comment_id,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can delete tablature comments")
        if status_code == 404:
            raise NotFoundError("Comment not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        return bool(payload.get("deleted"))
