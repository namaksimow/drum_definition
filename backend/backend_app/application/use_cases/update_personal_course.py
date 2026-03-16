from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, NotFoundError, ValidationError
from backend_app.domain.models import CourseItem


class UpdatePersonalCourseUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> CourseItem:
        status_code, payload = await self.postgres_service.update_personal_course(
            token=token,
            course_id=course_id,
            title=title,
            description=description,
            visibility=visibility,
            tags=tags,
            cover_image_path=cover_image_path,
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

        course = payload.get("course")
        if not isinstance(course, dict):
            raise DataIntegrityError("Course payload missing")

        raw_tags = course.get("tags")
        tags_list = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
        return CourseItem(
            id=int(course.get("id")),
            title=str(course.get("title") or ""),
            description=str(course["description"]) if course.get("description") is not None else None,
            author=str(course.get("author") or "unknown"),
            visibility=str(course.get("visibility") or "private"),
            tags=tags_list,
            cover_image_path=(
                str(course["cover_image_path"]) if course.get("cover_image_path") is not None else None
            ),
            created_at=str(course.get("created_at") or ""),
            updated_at=str(course.get("updated_at") or ""),
        )
