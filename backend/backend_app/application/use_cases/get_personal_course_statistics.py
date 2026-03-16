from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import (
    AuthenticationError,
    DataIntegrityError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
)
from backend_app.domain.models import CourseLessonCompletionStatItem, CourseStatisticsItem, CourseVisitorStatItem


class GetPersonalCourseStatisticsUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        course_id: int,
    ) -> CourseStatisticsItem:
        status_code, payload = await self.postgres_service.get_personal_course_statistics(
            token=token,
            course_id=course_id,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only author can view course statistics")
        if status_code == 404:
            raise NotFoundError("Course not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        raw_stats = payload.get("stats")
        if not isinstance(raw_stats, dict):
            raise DataIntegrityError("Course statistics payload is invalid")

        raw_visitors = raw_stats.get("visitors")
        if not isinstance(raw_visitors, list):
            raw_visitors = []
        visitors: list[CourseVisitorStatItem] = []
        for item in raw_visitors:
            if not isinstance(item, dict):
                continue
            first_visit_at = item.get("first_visit_at")
            if first_visit_at is None:
                continue
            try:
                visitors.append(
                    CourseVisitorStatItem(
                        user_id=int(item.get("user_id")),
                        user_name=str(item.get("user_name") or "unknown"),
                        first_visit_at=str(first_visit_at),
                    )
                )
            except Exception:
                continue

        raw_completions = raw_stats.get("lesson_completions")
        if not isinstance(raw_completions, list):
            raw_completions = []
        lesson_completions: list[CourseLessonCompletionStatItem] = []
        for item in raw_completions:
            if not isinstance(item, dict):
                continue
            completed_at = item.get("completed_at")
            if completed_at is None:
                continue
            try:
                lesson_completions.append(
                    CourseLessonCompletionStatItem(
                        user_id=int(item.get("user_id")),
                        user_name=str(item.get("user_name") or "unknown"),
                        lesson_id=int(item.get("lesson_id")),
                        lesson_title=str(item.get("lesson_title") or ""),
                        completed_at=str(completed_at),
                    )
                )
            except Exception:
                continue

        return CourseStatisticsItem(
            course_id=int(raw_stats.get("course_id")),
            course_title=str(raw_stats.get("course_title") or ""),
            visitors=visitors,
            lesson_completions=lesson_completions,
        )
