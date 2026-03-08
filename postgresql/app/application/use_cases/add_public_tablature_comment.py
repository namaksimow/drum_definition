from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class AddPublicTablatureCommentUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int, user_id: int, content: str) -> dict | None:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Comment content is required")
        return await self.gateway.add_public_tablature_comment(
            tablature_id=tablature_id,
            user_id=user_id,
            content=normalized_content,
        )
