from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import CourseVisitMarkerItem


class TrackPersonalCourseVisitUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        course_id: int,
    ) -> CourseVisitMarkerItem:
        status_code, payload = await self.postgres_service.track_personal_course_visit(
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

        item = payload.get("visit")
        if not isinstance(item, dict):
            raise DataIntegrityError("Course visit payload is invalid")

        first_visit_at = item.get("first_visit_at")
        return CourseVisitMarkerItem(
            user_id=int(item.get("user_id")),
            course_id=int(item.get("course_id")),
            is_first_visit=bool(item.get("is_first_visit")),
            first_visit_at=str(first_visit_at) if first_visit_at is not None else None,
        )
