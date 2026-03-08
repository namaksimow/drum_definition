from __future__ import annotations

import json

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import JsonArtifact


class DownloadPublicTablatureJsonUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(self, *, tablature_id: int) -> JsonArtifact:
        status_code, payload = await self.postgres_service.get_public_tablature(tablature_id=tablature_id)
        if status_code == 404:
            raise NotFoundError("Public tablature not found")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        tablature = payload.get("tablature")
        if not isinstance(tablature, dict):
            raise DataIntegrityError("Tablature payload missing")

        json_format = tablature.get("json_format")
        if not isinstance(json_format, (dict, list)):
            raise DataIntegrityError("Tablature JSON is missing")

        content = json.dumps(json_format, ensure_ascii=False, indent=2).encode("utf-8")
        return JsonArtifact(
            content=content,
            download_filename=f"community-tablature-{tablature_id}.json",
        )
