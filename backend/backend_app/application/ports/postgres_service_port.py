from __future__ import annotations

from typing import Protocol


class PostgresServicePort(Protocol):
    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> tuple[int, dict | str]:
        ...

    async def list_public_courses(self, *, query: str | None, limit: int, offset: int) -> tuple[int, dict | str]:
        ...

    async def create_course(
        self,
        *,
        token: str,
        title: str,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def list_personal_courses(
        self,
        *,
        token: str,
        query: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        ...

    async def update_personal_course(
        self,
        *,
        token: str,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def delete_personal_course(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        ...

    async def list_public_course_lessons(self, *, course_id: int) -> tuple[int, dict | str]:
        ...

    async def list_personal_course_lessons(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        ...

    async def create_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def update_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
        title: str | None = None,
        content: str | None = None,
        position: int | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def delete_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
    ) -> tuple[int, dict | str]:
        ...

    async def list_personal_course_lesson_progress(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        ...

    async def set_personal_course_lesson_progress(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
        completed: bool,
    ) -> tuple[int, dict | str]:
        ...

    async def track_personal_course_visit(
        self,
        *,
        token: str,
        course_id: int,
    ) -> tuple[int, dict | str]:
        ...

    async def get_personal_course_statistics(
        self,
        *,
        token: str,
        course_id: int,
    ) -> tuple[int, dict | str]:
        ...

    async def get_public_tablature(self, *, tablature_id: int) -> tuple[int, dict | str]:
        ...

    async def list_public_tablature_comments(
        self,
        *,
        tablature_id: int,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        ...

    async def create_public_tablature_comment(
        self,
        *,
        token: str,
        tablature_id: int,
        content: str,
    ) -> tuple[int, dict | str]:
        ...

    async def get_public_tablature_reactions(
        self,
        *,
        tablature_id: int,
        token: str | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def set_public_tablature_reaction(
        self,
        *,
        token: str,
        tablature_id: int,
        reaction_type: str,
    ) -> tuple[int, dict | str]:
        ...

    async def register_user(self, *, email: str, password: str, nickname: str) -> tuple[int, dict | str]:
        ...

    async def login_user(self, *, email: str, password: str) -> tuple[int, dict | str]:
        ...

    async def get_current_user(self, *, token: str) -> tuple[int, dict | str]:
        ...

    async def update_current_user(self, *, token: str, nickname: str) -> tuple[int, dict | str]:
        ...

    async def get_personal_author_role_request(self, *, token: str) -> tuple[int, dict | str]:
        ...

    async def create_personal_author_role_request(
        self,
        *,
        token: str,
        message: str,
    ) -> tuple[int, dict | str]:
        ...

    async def list_admin_author_role_requests(
        self,
        *,
        token: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        ...

    async def update_admin_author_role_request(
        self,
        *,
        token: str,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> tuple[int, dict | str]:
        ...

    async def list_personal_tablatures(
        self,
        *,
        token: str,
        query: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        ...

    async def get_personal_tablature(self, *, token: str, tablature_id: int) -> tuple[int, dict | str]:
        ...

    async def update_personal_tablature(
        self,
        *,
        token: str,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> tuple[int, dict | str]:
        ...
