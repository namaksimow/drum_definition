from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError
from backend_app.domain.models import AdminAuthorRoleRequestItem


class ListAdminAuthorRoleRequestsUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[AdminAuthorRoleRequestItem]:
        status_code, payload = await self.postgres_service.list_admin_author_role_requests(
            token=token,
            status=status,
            limit=limit,
            offset=offset,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can view author role requests")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise DataIntegrityError("Author role requests payload is invalid")

        result: list[AdminAuthorRoleRequestItem] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    AdminAuthorRoleRequestItem(
                        id=int(item.get("id")),
                        user_id=int(item.get("user_id")),
                        user_email=str(item.get("user_email") or ""),
                        user_nickname=str(item.get("user_nickname") or ""),
                        message=str(item.get("message") or ""),
                        status=str(item.get("status") or "pending"),
                        admin_message=(str(item.get("admin_message")) if item.get("admin_message") is not None else None),
                        created_at=str(item.get("created_at") or ""),
                        updated_at=str(item.get("updated_at") or ""),
                    )
                )
            except Exception:
                continue
        return result
