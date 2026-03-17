from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class ListAdminUsersUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        role: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        normalized_role: str | None = None
        if role is not None and role.strip():
            normalized_role = role.strip().lower()
            if normalized_role not in {"all", "user", "author"}:
                raise ValueError("Role filter must be all, user or author")

        return await self.gateway.list_admin_users(
            role=normalized_role,
            query=query,
            limit=int(limit),
            offset=int(offset),
        )
