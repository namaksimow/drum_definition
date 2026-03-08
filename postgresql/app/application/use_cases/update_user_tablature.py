from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class UpdateUserTablatureUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> dict | None:
        return await self.gateway.update_user_tablature(
            user_id=user_id,
            tablature_id=tablature_id,
            track_file_name=track_file_name,
            visibility=visibility,
            json_format=json_format,
        )
