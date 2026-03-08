from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ValidationError


class UpdateCurrentUserUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, nickname: str) -> dict:
        status_code, payload = await self.postgres_service.update_current_user(
            token=token,
            nickname=nickname,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 400:
            raise ValidationError("Invalid nickname")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        user = payload.get("user")
        if not isinstance(user, dict):
            raise DataIntegrityError("Auth payload missing user")
        return user
