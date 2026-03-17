from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class DeleteAdminTablatureUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int) -> bool:
        return await self.gateway.delete_admin_tablature(tablature_id=int(tablature_id))
