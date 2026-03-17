from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListAdminCourseLessonsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, course_id: int) -> list[dict] | None:
        return await self.gateway.list_admin_course_lessons(course_id=int(course_id))
