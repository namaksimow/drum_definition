from __future__ import annotations

from typing import Protocol


class MlServicePort(Protocol):
    async def submit_upload(
        self,
        *,
        filename: str,
        data: bytes,
        content_type: str,
        user_id: int | None = None,
        tablature_name: str | None = None,
    ) -> dict:
        ...

    async def get_job(self, *, job_id: str) -> tuple[int, dict | str]:
        ...

    async def get_tablature(self, *, job_id: str) -> tuple[int, dict | str]:
        ...

    async def get_pdf(self, *, job_id: str) -> tuple[int, bytes | dict | str]:
        ...
