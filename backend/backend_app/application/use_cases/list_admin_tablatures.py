from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError


class ListAdminTablaturesUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        status_code, payload = await self.postgres_service.list_admin_tablatures(
            token=token,
            query=query,
            limit=limit,
            offset=offset,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can view tablatures")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise DataIntegrityError("Admin tablatures payload is invalid")

        result: list[dict] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    {
                        "id": int(item.get("id")),
                        "task_id": int(item.get("task_id")),
                        "track_file_name": str(item.get("track_file_name") or ""),
                        "author": str(item.get("author") or "unknown"),
                        "visibility": str(item.get("visibility") or "private"),
                        "result_path": str(item["result_path"]) if item.get("result_path") else None,
                        "created_at": str(item.get("created_at") or ""),
                        "updated_at": str(item.get("updated_at") or ""),
                        "comments_count": int(item.get("comments_count") or 0),
                        "reactions_like_count": int(item.get("reactions_like_count") or 0),
                        "reactions_fire_count": int(item.get("reactions_fire_count") or 0),
                        "reactions_wow_count": int(item.get("reactions_wow_count") or 0),
                    }
                )
            except Exception:
                continue
        return result
