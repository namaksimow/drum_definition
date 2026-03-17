from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import (
    AuthenticationError,
    DataIntegrityError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class UpdateAdminUserAccountUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        user_id: int,
        email: str | None = None,
        nickname: str | None = None,
        role: str | None = None,
    ) -> dict:
        status_code, payload = await self.postgres_service.update_admin_user_account(
            token=token,
            user_id=user_id,
            email=email,
            nickname=nickname,
            role=role,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can update users")
        if status_code == 404:
            raise NotFoundError("User not found")
        if status_code == 400:
            detail = ""
            if isinstance(payload, dict):
                raw_detail = payload.get("detail")
                if isinstance(raw_detail, str):
                    detail = raw_detail.strip()
            raise ValidationError(detail or "Invalid user update payload")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        user = payload.get("user")
        if not isinstance(user, dict):
            raise DataIntegrityError("User payload missing")
        return user
