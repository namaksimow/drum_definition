from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, ForbiddenError, NotFoundError
from backend_app.domain.models import CourseLessonItem


class ListAdminCourseLessonsUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, course_id: int) -> list[CourseLessonItem]:
        status_code, payload = await self.postgres_service.list_admin_course_lessons(
            token=token,
            course_id=course_id,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can view course lessons")
        if status_code == 404:
            raise NotFoundError("Course not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        items = payload.get("items")
        if not isinstance(items, list):
            raise DataIntegrityError("Course lessons payload is invalid")

        result: list[CourseLessonItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    CourseLessonItem(
                        id=int(item.get("id")),
                        course_id=int(item.get("course_id")),
                        title=str(item.get("title") or ""),
                        content=str(item.get("content") or ""),
                        position=int(item.get("position") or 1),
                        created_at=str(item.get("created_at") or ""),
                        updated_at=str(item.get("updated_at") or ""),
                    )
                )
            except Exception:
                continue
        return result
