from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class SetPublicTablatureReactionUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, tablature_id: int, user_id: int, reaction_type: str) -> dict | None:
        normalized_reaction = reaction_type.strip().lower()
        if normalized_reaction not in {"like", "fire", "wow"}:
            raise ValueError("Unsupported reaction type")
        return await self.gateway.set_public_tablature_reaction(
            tablature_id=tablature_id,
            user_id=user_id,
            reaction_type=normalized_reaction,
        )
