from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError, ValidationError


class ListAdminUsersUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        role: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        status_code, payload = await self.postgres_service.list_admin_users(
            token=token,
            role=role,
            query=query,
            limit=limit,
            offset=offset,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can view users")
        if status_code == 400:
            detail = ""
            if isinstance(payload, dict):
                raw_detail = payload.get("detail")
                if isinstance(raw_detail, str):
                    detail = raw_detail.strip()
            raise ValidationError(detail or "Invalid users filter")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise DataIntegrityError("Admin users payload is invalid")

        result: list[dict] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    {
                        "id": int(item.get("id")),
                        "email": str(item.get("email") or ""),
                        "nickname": str(item.get("nickname") or ""),
                        "role": str(item.get("role") or "user"),
                    }
                )
            except Exception:
                continue
        return result
