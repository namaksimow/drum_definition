from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, NotFoundError, ValidationError
from backend_app.domain.models import CourseLessonItem


class CreatePersonalCourseLessonUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> CourseLessonItem:
        status_code, payload = await self.postgres_service.create_personal_course_lesson(
            token=token,
            course_id=course_id,
            title=title,
            content=content,
            position=position,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 404:
            raise NotFoundError("Course not found")
        if status_code == 400:
            raise ValidationError(str(payload))
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        item = payload.get("lesson")
        if not isinstance(item, dict):
            raise DataIntegrityError("Lesson payload is invalid")

        return CourseLessonItem(
            id=int(item.get("id")),
            course_id=int(item.get("course_id")),
            title=str(item.get("title") or ""),
            content=str(item.get("content") or ""),
            position=int(item.get("position") or 1),
            created_at=str(item.get("created_at") or ""),
            updated_at=str(item.get("updated_at") or ""),
        )
