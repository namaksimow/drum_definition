from __future__ import annotations

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import AuthenticationError, DataIntegrityError, ExternalServiceError
from backend_app.domain.models import CommunityTablatureItem


class ListPersonalTablaturesUseCase:
    def __init__(self, postgres_service: PostgresServicePort) -> None:
        self.postgres_service = postgres_service

    async def execute(
        self,
        *,
        token: str,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[CommunityTablatureItem]:
        status_code, payload = await self.postgres_service.list_personal_tablatures(
            token=token,
            query=query,
            limit=limit,
            offset=offset,
        )
        if status_code == 401:
            raise AuthenticationError("Invalid or expired token")
        if status_code != 200:
            raise ExternalServiceError(f"PostgreSQL service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("PostgreSQL service returned non-JSON payload")

        items = payload.get("items")
        if not isinstance(items, list):
            raise DataIntegrityError("Personal tablatures payload is invalid")

        result: list[CommunityTablatureItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    CommunityTablatureItem(
                        id=int(item.get("id")),
                        task_id=int(item.get("task_id")),
                        track_file_name=str(item.get("track_file_name") or ""),
                        author=str(item.get("author") or "unknown"),
                        result_path=str(item["result_path"]) if item.get("result_path") else None,
                        created_at=str(item.get("created_at") or ""),
                    )
                )
            except Exception:
                continue
        return result
