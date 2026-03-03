from __future__ import annotations

from typing import Protocol


class JobQueue(Protocol):
    async def publish(self, job_id: str) -> None:
        ...

    async def consume(self, timeout: float | None = None) -> str | None:
        ...

