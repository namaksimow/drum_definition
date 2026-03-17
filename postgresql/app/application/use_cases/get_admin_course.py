from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetAdminCourseUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, course_id: int) -> dict | None:
        return await self.gateway.get_admin_course(course_id=int(course_id))
