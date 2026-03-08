from __future__ import annotations

from typing import Protocol


class DatabaseGateway(Protocol):
    async def ping(self) -> bool:
        ...

    async def list_tables(self) -> list[str]:
        ...

    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> list[dict]:
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
