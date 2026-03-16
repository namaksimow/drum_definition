from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListUserCourseLessonsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int, course_id: int) -> list[dict] | None:
        return await self.gateway.list_user_course_lessons(
            user_id=int(user_id),
            course_id=int(course_id),
        )
