from __future__ import annotations

import asyncio

from ml_service.ports.queue import JobQueue


class MockQueue(JobQueue):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def publish(self, job_id: str) -> None:
        await self._queue.put(job_id)

    async def consume(self, timeout: float | None = None) -> str | None:
        if timeout is None:
            return await self._queue.get()

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

