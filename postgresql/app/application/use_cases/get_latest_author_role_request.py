from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class GetLatestAuthorRoleRequestUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int) -> dict | None:
        return await self.gateway.get_latest_author_role_request(user_id=int(user_id))
