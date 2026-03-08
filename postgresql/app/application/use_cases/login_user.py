from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway
from app.application.security import create_access_token, verify_password


class LoginUserUseCase:
    def __init__(
        self,
        gateway: DatabaseGateway,
        *,
        jwt_secret_key: str,
        jwt_algorithm: str,
        jwt_expire_minutes: int,
    ) -> None:
        self.gateway = gateway
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expire_minutes = int(jwt_expire_minutes)

    async def execute(self, *, email: str, password: str) -> dict:
        normalized_email = email.strip().lower()
        if not normalized_email or not password:
            raise ValueError("Email and password are required")
        if "@" not in normalized_email:
            raise ValueError("Invalid credentials")

        user = await self.gateway.get_user_by_email(email=normalized_email)
        if user is None:
            raise ValueError("Invalid credentials")

        encoded_password = str(user.get("password_hash") or "")
        if not verify_password(password, encoded_password):
            raise ValueError("Invalid credentials")

        user_id = int(user["id"])
        role_title = str(user.get("role_title") or "user")
        nickname = str(user.get("nickname") or "")
        access_token = create_access_token(
            user_id=user_id,
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            expire_minutes=self.jwt_expire_minutes,
            extra_claims={
                "email": str(user.get("email") or ""),
                "nickname": nickname,
                "role": role_title,
            },
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.jwt_expire_minutes * 60,
            "user": {
                "id": user_id,
                "email": str(user.get("email") or ""),
                "nickname": nickname,
                "role": role_title,
            },
        }
