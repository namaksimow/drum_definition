from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import DataIntegrityError, ExternalServiceError, NotFoundError


class ListPublicTablatureCommentsUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, tablature_id: int, limit: int, offset: int) -> list[dict]:
        status_code, payload = await self.postgres_service.list_public_tablature_comments(
            tablature_id=tablature_id,
            limit=limit,
            offset=offset,
        )
        if status_code == 404:
            raise NotFoundError("Public tablature not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        items = payload.get("items")
        if not isinstance(items, list):
            raise DataIntegrityError("Comments payload missing items")
        return items
