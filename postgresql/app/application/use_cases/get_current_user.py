from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway
from app.application.security import decode_access_token


class GetCurrentUserUseCase:
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

    async def execute(self, *, token: str) -> dict:
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

        user = await self.gateway.get_user_by_id(user_id=user_id)
        if user is None:
            raise ValueError("User not found")

        return {
            "id": int(user["id"]),
            "email": str(user.get("email") or ""),
            "nickname": str(user.get("nickname") or ""),
            "role": str(user.get("role_title") or "user"),
        }
