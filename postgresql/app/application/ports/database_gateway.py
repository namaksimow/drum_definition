from __future__ import annotations

from typing import Protocol


class DatabaseGateway(Protocol):
    async def ping(self) -> bool:
        ...

    async def list_tables(self) -> list[str]:
        ...

    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def list_public_courses(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def create_course(
        self,
        *,
        user_id: int,
        title: str,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> dict:
        ...

    async def list_user_courses(self, *, user_id: int, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def update_user_course(
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
        ...

    async def delete_user_course(self, *, user_id: int, course_id: int) -> bool:
        ...

    async def list_public_course_lessons(self, *, course_id: int) -> list[dict] | None:
        ...

    async def list_user_course_lessons(self, *, user_id: int, course_id: int) -> list[dict] | None:
        ...

    async def create_user_course_lesson(
        self,
        *,
        user_id: int,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> dict | None:
        ...

    async def update_user_course_lesson(
        self,
        *,
        user_id: int,
        course_id: int,
        lesson_id: int,
        title: str | None = None,
        content: str | None = None,
        position: int | None = None,
    ) -> dict | None:
        ...

    async def delete_user_course_lesson(self, *, user_id: int, course_id: int, lesson_id: int) -> bool:
        ...

    async def list_user_course_lesson_progress(self, *, user_id: int, course_id: int) -> list[dict] | None:
        ...

    async def set_user_course_lesson_progress(
        self,
        *,
        user_id: int,
        course_id: int,
        lesson_id: int,
        completed: bool,
    ) -> dict | None:
        ...

    async def track_user_course_visit(
        self,
        *,
        user_id: int,
        course_id: int,
    ) -> dict | None:
        ...

    async def get_author_course_statistics(
        self,
        *,
        author_user_id: int,
        course_id: int,
    ) -> dict | None:
        ...

    async def get_public_tablature(self, *, tablature_id: int) -> dict | None:
        ...

    async def list_public_tablature_comments(
        self,
        *,
        tablature_id: int,
        limit: int,
        offset: int,
    ) -> list[dict] | None:
        ...

    async def add_public_tablature_comment(
        self,
        *,
        tablature_id: int,
        user_id: int,
        content: str,
    ) -> dict | None:
        ...

    async def get_public_tablature_reactions(
        self,
        *,
        tablature_id: int,
        user_id: int | None = None,
    ) -> dict | None:
        ...

    async def set_public_tablature_reaction(
        self,
        *,
        tablature_id: int,
        user_id: int,
        reaction_type: str,
    ) -> dict | None:
        ...

    async def list_user_tablatures(self, *, user_id: int, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def get_user_tablature(self, *, user_id: int, tablature_id: int) -> dict | None:
        ...

    async def update_user_tablature(
        self,
        *,
        user_id: int,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> dict | None:
        ...

    async def get_user_by_email(self, *, email: str) -> dict | None:
        ...

    async def get_user_by_id(self, *, user_id: int) -> dict | None:
        ...

    async def update_user_nickname(self, *, user_id: int, nickname: str) -> dict | None:
        ...

    async def create_user(
        self,
        *,
        email: str,
        nickname: str,
        password_hash: str,
        role_title: str,
    ) -> dict:
        ...

    async def get_latest_author_role_request(self, *, user_id: int) -> dict | None:
        ...

    async def create_author_role_request(self, *, user_id: int, message: str) -> dict:
        ...

    async def list_admin_tablatures(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def list_admin_courses(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
        ...

    async def get_admin_tablature(self, *, tablature_id: int) -> dict | None:
        ...

    async def update_admin_tablature_visibility(
        self,
        *,
        tablature_id: int,
        visibility: str,
    ) -> dict | None:
        ...

    async def delete_admin_tablature(self, *, tablature_id: int) -> bool:
        ...

    async def list_admin_tablature_comments(
        self,
        *,
        tablature_id: int,
        limit: int,
        offset: int,
    ) -> list[dict] | None:
        ...

    async def delete_admin_tablature_comment(self, *, tablature_id: int, comment_id: int) -> bool:
        ...

    async def get_admin_course(self, *, course_id: int) -> dict | None:
        ...

    async def update_admin_course_visibility(
        self,
        *,
        course_id: int,
        visibility: str,
    ) -> dict | None:
        ...

    async def delete_admin_course(self, *, course_id: int) -> bool:
        ...

    async def list_admin_course_lessons(self, *, course_id: int) -> list[dict] | None:
        ...

    async def list_admin_users(
        self,
        *,
        role: str | None,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        ...

    async def update_admin_user_account(
        self,
        *,
        user_id: int,
        email: str | None = None,
        nickname: str | None = None,
        role: str | None = None,
    ) -> dict | None:
        ...

    async def delete_admin_user(self, *, user_id: int) -> bool:
        ...

    async def list_author_role_requests(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        ...

    async def update_author_role_request_status(
        self,
        *,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> dict | None:
        ...
