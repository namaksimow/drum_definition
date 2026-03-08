from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway
from app.application.security import decode_access_token


class UpdateCurrentUserNicknameUseCase:
    def __init__(
        self,
        gateway: DatabaseGateway,
        *,
        jwt_secret_key: str,
        jwt_algorithm: str,
    ) -> None:
        self.gateway = gateway
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm

    async def execute(self, *, token: str, nickname: str) -> dict:
        normalized_nickname = nickname.strip()
        if not normalized_nickname:
            raise ValueError("Nickname is required")

        payload = decode_access_token(
            token=token,
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
        )
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Token missing subject")
        try:
            user_id = int(subject)
        except Exception as exc:
            raise ValueError("Invalid token subject") from exc

        updated = await self.gateway.update_user_nickname(
            user_id=user_id,
            nickname=normalized_nickname,
        )
        if updated is None:
            raise ValueError("User not found")

        return {
            "id": int(updated["id"]),
            "email": str(updated.get("email") or ""),
            "nickname": str(updated.get("nickname") or ""),
            "role": str(updated.get("role_title") or "user"),
        }
