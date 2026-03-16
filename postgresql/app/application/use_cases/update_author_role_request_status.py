from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class UpdateAuthorRoleRequestStatusUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> dict | None:
        return await self.gateway.update_author_role_request_status(
            request_id=int(request_id),
            status=status,
            admin_message=admin_message,
        )
