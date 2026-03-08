from __future__ import annotations

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import JobInfoArtifact


class GetJobByIdUseCase:
    def __init__(self, ml_service: MlServicePort) -> None:
        self.ml_service = ml_service

    async def execute(self, *, job_id: str) -> JobInfoArtifact:
        status_code, payload = await self.ml_service.get_job(job_id=job_id)

        if status_code == 404:
            raise NotFoundError("Job not found")
        if status_code != 200:
            raise ExternalServiceError(f"ML service error: {payload}")
        if not isinstance(payload, dict):
            raise DataIntegrityError("ML service returned non-JSON payload")

        job = payload.get("job")
        if not isinstance(job, dict):
            raise DataIntegrityError("ML service payload missing job object")

        job_id_value = job.get("id")
        status = job.get("status")
        if not job_id_value or not status:
            raise DataIntegrityError("ML service payload missing id or status")

        return JobInfoArtifact(
            id=str(job_id_value),
            status=str(status),
            raw_payload=job,
        )
