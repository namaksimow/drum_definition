from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetPublicTablatureUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int) -> dict | None:
        return await self.gateway.get_public_tablature(tablature_id=tablature_id)
