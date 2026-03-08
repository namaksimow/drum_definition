from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetPublicTablatureReactionsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int, user_id: int | None = None) -> dict | None:
        return await self.gateway.get_public_tablature_reactions(
            tablature_id=tablature_id,
            user_id=user_id,
        )
