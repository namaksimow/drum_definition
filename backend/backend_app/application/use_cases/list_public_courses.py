from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import DataIntegrityError, ExternalServiceError
from backend_app.domain.models import CourseItem


class ListPublicCoursesUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, query: str | None, limit: int, offset: int) -> list[CourseItem]:
        status_code, payload = await self.postgres_service.list_public_courses(
            query=query,
            limit=limit,
            offset=offset,
        )
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        items = payload.get("items")
        if not isinstance(items, list):
            raise DataIntegrityError("Public courses payload is invalid")

        result: list[CourseItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                raw_tags = item.get("tags")
                tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
                result.append(
                    CourseItem(
                        id=int(item.get("id")),
                        title=str(item.get("title") or ""),
                        description=str(item["description"]) if item.get("description") is not None else None,
                        author=str(item.get("author") or "unknown"),
                        visibility=str(item.get("visibility") or "public"),
                        tags=tags,
                        cover_image_path=(
                            str(item["cover_image_path"]) if item.get("cover_image_path") is not None else None
                        ),
                        created_at=str(item.get("created_at") or ""),
                        updated_at=str(item.get("updated_at") or ""),
                    )
                )
            except Exception:
                continue
        return result
