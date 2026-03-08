from __future__ import annotations

from typing import Protocol


class TablatureStore(Protocol):
    async def save(self, job_id: str, tablature: dict) -> None:
        ...

    async def get(self, job_id: str) -> dict | None:
        ...

