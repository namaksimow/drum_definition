from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ValidationError


class LoginUserUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, email: str, password: str) -> dict:
        status_code, payload = await self.postgres_service.login_user(
            email=email,
            password=password,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid credentials")
        if status_code == 400:
            raise ValidationError(str(payload))
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        if "access_token" not in payload:
            raise DataIntegrityError("Login payload missing token")
        return payload
