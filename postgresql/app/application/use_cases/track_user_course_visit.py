from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class TrackUserCourseVisitUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        course_id: int,
    ) -> dict | None:
        return await self.gateway.track_user_course_visit(
            user_id=int(user_id),
            course_id=int(course_id),
        )
