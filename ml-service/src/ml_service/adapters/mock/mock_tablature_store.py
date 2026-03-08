from __future__ import annotations

import asyncio

from ml_service.ports.tablature_store import TablatureStore


class MockTablatureStore(TablatureStore):
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def save(self, job_id: str, tablature: dict) -> None:
        async with self._lock:
            self._store[job_id] = tablature

    async def get(self, job_id: str) -> dict | None:
        async with self._lock:
            return self._store.get(job_id)

