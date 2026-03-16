from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListPublicCourseLessonsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, course_id: int) -> list[dict] | None:
        return await self.gateway.list_public_course_lessons(course_id=course_id)
