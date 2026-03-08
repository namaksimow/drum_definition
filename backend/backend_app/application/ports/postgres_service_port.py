from __future__ import annotations

from typing import Protocol


class PostgresServicePort(Protocol):
    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> tuple[int, dict | str]:
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
