from __future__ import annotations

from typing import Protocol


class MlServicePort(Protocol):
    async def submit_upload(self, *, filename: str, data: bytes, content_type: str) -> dict:
        ...

    async def get_job(self, *, job_id: str) -> tuple[int, dict | str]:
        ...

