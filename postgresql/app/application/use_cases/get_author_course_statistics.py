from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetAuthorCourseStatisticsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        author_user_id: int,
        course_id: int,
    ) -> dict | None:
        return await self.gateway.get_author_course_statistics(
            author_user_id=int(author_user_id),
            course_id=int(course_id),
        )
