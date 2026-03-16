from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, ConflictError, DataIntegrityError, ExternalServiceError, ValidationError
from backend_app.domain.models import AuthorRoleRequestItem


class CreatePersonalAuthorRoleRequestUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, message: str) -> AuthorRoleRequestItem:
        status_code, payload = await self.postgres_service.create_personal_author_role_request(
            token=token,
            message=message,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 409:
            raise ConflictError("Заявка уже отправлена или роль автора уже есть")
        if status_code == 400:
            raise ValidationError("Некорректный текст заявки")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_item = payload.get("request")
        if not isinstance(raw_item, dict):
            raise DataIntegrityError("Author role request payload is invalid")

        return AuthorRoleRequestItem(
            id=int(raw_item.get("id")),
            user_id=int(raw_item.get("user_id")),
            message=str(raw_item.get("message") or ""),
            status=str(raw_item.get("status") or "pending"),
            admin_message=(str(raw_item.get("admin_message")) if raw_item.get("admin_message") is not None else None),
            created_at=str(raw_item.get("created_at") or ""),
            updated_at=str(raw_item.get("updated_at") or ""),
        )
