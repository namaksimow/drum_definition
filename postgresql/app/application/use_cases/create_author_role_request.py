from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class CreateAuthorRoleRequestUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, user_id: int, message: str) -> dict:
        return await self.gateway.create_author_role_request(
            user_id=int(user_id),
            message=message,
        )
