from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import (
    AuthenticationError,
    DataIntegrityError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class UpdateAdminTablatureVisibilityUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, token: str, tablature_id: int, visibility: str) -> dict:
        status_code, payload = await self.postgres_service.update_admin_tablature_visibility(
            token=token,
            tablature_id=tablature_id,
            visibility=visibility,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 403:
            raise ForbiddenError("Only admin can update tablatures")
        if status_code == 404:
            raise NotFoundError("Tablature not found")
        if status_code == 400:
            detail = ""
            if isinstance(payload, dict):
                raw_detail = payload.get("detail")
                if isinstance(raw_detail, str):
                    detail = raw_detail.strip()
            raise ValidationError(detail or "Invalid visibility")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        tablature = payload.get("tablature")
        if not isinstance(tablature, dict):
            raise DataIntegrityError("Tablature payload missing")
        return tablature
