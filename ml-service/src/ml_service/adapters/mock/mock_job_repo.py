from __future__ import annotations

import asyncio

from ml_service.domain.models import Job, utc_now_iso
from ml_service.ports.job_repo import JobRepo


class MockJobRepo(JobRepo):
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def list(self) -> list[Job]:
        async with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    async def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result_manifest: dict | None = None,
        error: str | None = None,
    ) -> Job | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None

            if status is not None:
                job.status = status  # type: ignore[assignment]
            if result_manifest is not None:
                job.result_manifest = result_manifest
            job.error = error
            job.updated_at = utc_now_iso()
            return job
