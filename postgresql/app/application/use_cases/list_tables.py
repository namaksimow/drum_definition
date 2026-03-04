from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListTablesUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self) -> list[str]:
        return await self.gateway.list_tables()
