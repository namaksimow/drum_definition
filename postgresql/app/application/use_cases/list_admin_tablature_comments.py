from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListAdminTablatureCommentsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int, limit: int, offset: int) -> list[dict] | None:
        return await self.gateway.list_admin_tablature_comments(
            tablature_id=int(tablature_id),
            limit=int(limit),
            offset=int(offset),
        )
