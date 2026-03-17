from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class DeleteAdminCourseUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, course_id: int) -> bool:
        return await self.gateway.delete_admin_course(course_id=int(course_id))
