from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListAdminTablaturesUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        return await self.gateway.list_admin_tablatures(
            query=query,
            limit=int(limit),
            offset=int(offset),
        )
