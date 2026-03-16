from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import CourseLessonProgressItem


class ListPersonalCourseLessonProgressUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, course_id: int) -> list[CourseLessonProgressItem]:
        status_code, payload = await self.postgres_service.list_personal_course_lesson_progress(
            token=token,
            course_id=course_id,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 404:
            raise NotFoundError("Course not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        items = payload.get("items")
        if not isinstance(items, list):
            raise DataIntegrityError("Lesson progress payload is invalid")

        result: list[CourseLessonProgressItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                completed_at = item.get("completed_at")
                updated_at = item.get("updated_at")
                result.append(
                    CourseLessonProgressItem(
                        lesson_id=int(item.get("lesson_id")),
                        is_completed=bool(item.get("is_completed")),
                        completed_at=str(completed_at) if completed_at is not None else None,
                        updated_at=str(updated_at) if updated_at is not None else None,
                    )
                )
            except Exception:
                continue
        return result
