from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListAuthorRoleRequestsUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        return await self.gateway.list_author_role_requests(
            status=status,
            limit=int(limit),
            offset=int(offset),
        )
