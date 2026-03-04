from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway
from app.domain.errors import DatabaseUnavailableError


class CheckDbHealthUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self) -> None:
        if not await self.gateway.ping():
            raise DatabaseUnavailableError("Database is unavailable")
