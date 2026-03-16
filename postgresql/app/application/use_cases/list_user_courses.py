from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListUserCoursesUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int, query: str | None, limit: int, offset: int) -> list[dict]:
        return await self.gateway.list_user_courses(
            user_id=user_id,
            query=query,
            limit=limit,
            offset=offset,
        )
