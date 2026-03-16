from __future__ import annotations

from app.application.ports.database_gateway import DatabaseGateway


class CreateCourseUseCase:
    def __init__(self, gateway: DatabaseGateway) -> None:
        self.gateway = gateway

    async def execute(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> dict:
        normalized_title = title.strip()
        if not normalized_title:
            raise ValueError("Course title is required")

        normalized_description = None
        if description is not None:
            normalized_description = description.strip() or None

        normalized_visibility = (visibility or "public").strip().lower()
        if normalized_visibility not in {"public", "private"}:
            raise ValueError("Visibility must be public or private")

        normalized_tags: list[str] = []
        for raw_tag in tags or []:
            tag = str(raw_tag).strip().lower()
            if not tag:
                continue
            if tag not in normalized_tags:
                normalized_tags.append(tag)

        normalized_cover = None
        if cover_image_path is not None:
            normalized_cover = cover_image_path.strip() or None

        return await self.gateway.create_course(
            user_id=int(user_id),
            title=normalized_title,
            description=normalized_description,
            visibility=normalized_visibility,
            tags=normalized_tags,
            cover_image_path=normalized_cover,
        )
