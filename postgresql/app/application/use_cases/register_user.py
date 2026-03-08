from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway
from app.application.security import hash_password


class RegisterUserUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(self, *, email: str, password: str, nickname: str) -> dict:
        normalized_email = email.strip().lower()
        normalized_nickname = nickname.strip()
        if not normalized_email:
            raise ValueError("Email is required")
        if "@" not in normalized_email:
            raise ValueError("Invalid email")
        if len(password) < 6:
            raise ValueError("Password must contain at least 6 characters")
        if not normalized_nickname:
            raise ValueError("Nickname is required")

        existing = await self.gateway.get_user_by_email(email=normalized_email)
        if existing is not None:
            raise ValueError("User with this email already exists")

        created = await self.gateway.create_user(
            email=normalized_email,
            nickname=normalized_nickname,
            password_hash=hash_password(password),
            role_title="user",
        )
        return {
            "id": int(created["id"]),
            "email": str(created["email"]),
            "nickname": str(created["nickname"]),
            "role": str(created.get("role_title") or "user"),
        }
