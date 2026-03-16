from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class UpdateUserCourseUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> dict | None:
        normalized_visibility: str | None = None
        if visibility is not None:
            normalized_visibility = visibility.strip().lower()
            if normalized_visibility not in {"public", "private"}:
                raise ValueError("Visibility must be public or private")

        normalized_tags: list[str] | None = None
        if tags is not None:
            normalized_tags = []
            seen: set[str] = set()
            for raw_tag in tags:
                tag = str(raw_tag).strip().lower()
                if not tag or tag in seen:
                    continue
                seen.add(tag)
                normalized_tags.append(tag)

        return await self.gateway.update_user_course(
            user_id=int(user_id),
            course_id=int(course_id),
            title=title,
            description=description,
            visibility=normalized_visibility,
            tags=normalized_tags,
            cover_image_path=cover_image_path,
        )
