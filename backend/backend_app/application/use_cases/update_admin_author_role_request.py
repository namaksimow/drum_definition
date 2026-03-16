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
from backend_app.domain.models import AdminAuthorRoleRequestItem


class UpdateAdminAuthorRoleRequestUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> AdminAuthorRoleRequestItem:
        status_code, payload = await self.postgres_service.update_admin_author_role_request(
            token=token,
            request_id=request_id,
            status=status,
            admin_message=admin_message,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can update author role requests")
        if status_code == 404:
            raise NotFoundError("Author role request not found")
        if status_code == 400:
            detail = ""
            if isinstance(payload, dict):
                raw_detail = payload.get("detail")
                if isinstance(raw_detail, str):
                    detail = raw_detail.strip()
            raise ValidationError(detail or "Invalid status or admin message")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_item = payload.get("request")
        if not isinstance(raw_item, dict):
            raise DataIntegrityError("Author role request payload is invalid")

        return AdminAuthorRoleRequestItem(
            id=int(raw_item.get("id")),
            user_id=int(raw_item.get("user_id")),
            user_email=str(raw_item.get("user_email") or ""),
            user_nickname=str(raw_item.get("user_nickname") or ""),
            message=str(raw_item.get("message") or ""),
            status=str(raw_item.get("status") or "pending"),
            admin_message=(str(raw_item.get("admin_message")) if raw_item.get("admin_message") is not None else None),
            created_at=str(raw_item.get("created_at") or ""),
            updated_at=str(raw_item.get("updated_at") or ""),
        )
