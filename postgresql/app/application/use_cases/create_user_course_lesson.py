from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class CreateUserCourseLessonUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> dict | None:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Lesson title is required")

        normalized_content = None if content is None else content.strip()
        normalized_position = None if position is None else int(position)
        if normalized_position is not None and normalized_position < 1:
            raise ValueError("Lesson position must be >= 1")

        return await self.gateway.create_user_course_lesson(
            user_id=int(user_id),
            course_id=int(course_id),
            title=normalized_title,
            content=normalized_content,
            position=normalized_position,
        )
