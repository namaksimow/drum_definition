from __future__ import annotations

from typing import Protocol


class DatabaseGateway(Protocol):
    async def ping(self) -> bool:
        ...

    async def list_tables(self) -> list[str]:
        ...
