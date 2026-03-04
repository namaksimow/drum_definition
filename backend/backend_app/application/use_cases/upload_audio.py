from __future__ import annotations

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import DataIntegrityError, ExternalServiceError, ValidationError
from backend_app.domain.models import UploadedJob


class UploadAudioUseCase:
    def __init__(self, ml_service: MlServicePort) -> None:
        self.ml_service = ml_service

    async def execute(self, *, filename: str | None, data: bytes, content_type: str) -> UploadedJob:
        if not filename:
            raise ValidationError("Filename is required")
        if not data:
            raise ValidationError("File is empty")

        payload = await self.ml_service.submit_upload(
            filename=filename,
            data=data,
            content_type=content_type or "application/octet-stream",
        )
        job = payload.get("job")
        if not isinstance(job, dict):
            raise DataIntegrityError("ML service returned invalid job payload")

        job_id = job.get("id")
        status = job.get("status")
        if not job_id or not status:
            raise ExternalServiceError("ML service payload missing job id or status")

        return UploadedJob(
            id=str(job_id),
            status=str(status),
            raw_payload=payload,
        )

