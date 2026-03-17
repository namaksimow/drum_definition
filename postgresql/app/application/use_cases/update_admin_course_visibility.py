from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class UpdateAdminCourseVisibilityUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        course_id: int,
        visibility: str,
    ) -> dict | None:
        normalized_visibility = visibility.strip().lower()
        if normalized_visibility not in {"public", "private"}:
            raise ValueError("Visibility must be public or private")

        return await self.gateway.update_admin_course_visibility(
            course_id=int(course_id),
            visibility=normalized_visibility,
        )
