from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError


class ListAdminCoursesUseCase:
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
        status_code, payload = await self.postgres_service.list_admin_courses(
            token=token,
            query=query,
            limit=limit,
            offset=offset,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can view courses")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise DataIntegrityError("Admin courses payload is invalid")

        result: list[dict] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                raw_tags = item.get("tags")
                tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
                result.append(
                    {
                        "id": int(item.get("id")),
                        "title": str(item.get("title") or ""),
                        "description": str(item["description"]) if item.get("description") is not None else None,
                        "author": str(item.get("author") or "unknown"),
                        "visibility": str(item.get("visibility") or "private"),
                        "tags": tags,
                        "cover_image_path": (
                            str(item["cover_image_path"]) if item.get("cover_image_path") is not None else None
                        ),
                        "created_at": str(item.get("created_at") or ""),
                        "updated_at": str(item.get("updated_at") or ""),
                    }
                )
            except Exception:
                continue
        return result
