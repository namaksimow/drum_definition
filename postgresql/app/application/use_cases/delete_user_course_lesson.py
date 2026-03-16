from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class DeleteUserCourseLessonUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int, course_id: int, lesson_id: int) -> bool:
        return await self.gateway.delete_user_course_lesson(
            user_id=int(user_id),
            course_id=int(course_id),
            lesson_id=int(lesson_id),
        )
