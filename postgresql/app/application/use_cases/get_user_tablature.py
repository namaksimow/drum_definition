from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetUserTablatureUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int, tablature_id: int) -> dict | None:
        return await self.gateway.get_user_tablature(
            user_id=user_id,
            tablature_id=tablature_id,
        )
