from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListPublicTablatureCommentsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int, limit: int, offset: int) -> list[dict] | None:
        return await self.gateway.list_public_tablature_comments(
            tablature_id=tablature_id,
            limit=limit,
            offset=offset,
        )
