from __future__ import annotations

from typing import Protocol

from ml_service.domain.models import Job, JobStatus


class JobRepo(Protocol):
    async def create(self, job: Job) -> None:
        ...

    async def get(self, job_id: str) -> Job | None:
        ...

    async def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        result_manifest: dict | None = None,
        error: str | None = None,
    ) -> Job | None:
        ...

