from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class UpdateAdminUserAccountUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        email: str | None = None,
        nickname: str | None = None,
        role: str | None = None,
    ) -> dict | None:
        normalized_email: str | None = None
        if email is not None:
            normalized_email = email.strip().lower()
            if not normalized_email or "@" not in normalized_email:
                raise ValueError("Email is invalid")

        normalized_nickname: str | None = None
        if nickname is not None:
            normalized_nickname = nickname.strip()
            if not normalized_nickname:
                raise ValueError("Nickname is required")

        normalized_role: str | None = None
        if role is not None:
            normalized_role = role.strip().lower()
            if normalized_role not in {"user", "author"}:
                raise ValueError("Role must be user or author")

        return await self.gateway.update_admin_user_account(
            user_id=int(user_id),
            email=normalized_email,
            nickname=normalized_nickname,
            role=normalized_role,
        )
