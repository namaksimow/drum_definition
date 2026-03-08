from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import ConflictError, DataIntegrityError, ExternalServiceError, ValidationError


class RegisterUserUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, email: str, password: str, nickname: str) -> dict:
        status_code, payload = await self.postgres_service.register_user(
            email=email,
            password=password,
            nickname=nickname,
        )
        if status_code == 409:
            raise ConflictError("User with this email already exists")
        if status_code == 400:
            raise ValidationError(str(payload))
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        user = payload.get("user")
        if not isinstance(user, dict):
            raise DataIntegrityError("Register payload missing user")
        return user
