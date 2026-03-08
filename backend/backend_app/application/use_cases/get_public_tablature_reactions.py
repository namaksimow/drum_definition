from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, NotFoundError


class GetPublicTablatureReactionsUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, tablature_id: int, token: str | None = None) -> dict:
        status_code, payload = await self.postgres_service.get_public_tablature_reactions(
            tablature_id=tablature_id,
            token=token,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 404:
            raise NotFoundError("Public tablature not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        reactions = payload.get("reactions")
        if not isinstance(reactions, dict):
            raise DataIntegrityError("Reactions payload missing")
        return reactions
