from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DataIntegrityError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


class UpdatePersonalTablatureUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> dict:
        status_code, payload = await self.postgres_service.update_personal_tablature(
            token=token,
            tablature_id=tablature_id,
            track_file_name=track_file_name,
            visibility=visibility,
            json_format=json_format,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code == 404:
            raise NotFoundError("Tablature not found")
        if status_code == 409:
            raise ConflictError("Tablature with this name already exists")
        if status_code == 400:
            raise ValidationError("Invalid tablature update payload")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")
        tablature = payload.get("tablature")
        if not isinstance(tablature, dict):
            raise DataIntegrityError("Tablature payload missing")
        return tablature
