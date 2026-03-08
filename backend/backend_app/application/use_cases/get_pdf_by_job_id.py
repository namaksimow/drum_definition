from __future__ import annotations

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import ConflictError, DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import PdfArtifact


class GetPdfByJobIdUseCase:
    def __init__(self, ml_service: MlServicePort) -> None:
        self.ml_service = ml_service

    async def execute(self, *, job_id: str) -> PdfArtifact:
        status_code, payload = await self.ml_service.get_pdf(job_id=job_id)

        if status_code == 404:
            raise NotFoundError("Job or PDF not found")
        if status_code == 409:
            raise ConflictError("Job is not ready yet")

        if status_code != 200:
            raise ExternalServiceError(f"ML service error: {payload}")

        if not isinstance(payload, bytes):
            raise DataIntegrityError("ML service returned non-binary PDF payload")

        return PdfArtifact(
            content=payload,
            download_filename=f"{job_id}.pdf",
        )
