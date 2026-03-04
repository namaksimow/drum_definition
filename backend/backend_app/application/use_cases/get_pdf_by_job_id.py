from __future__ import annotations

from pathlib import Path

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import ConflictError, DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import PdfArtifact


class GetPdfByJobIdUseCase:
    def __init__(self, ml_service: MlServicePort) -> None:
        self.ml_service = ml_service

    async def execute(self, *, job_id: str) -> PdfArtifact:
        status_code, payload = await self.ml_service.get_job(job_id=job_id)

        if status_code == 404:
            raise NotFoundError("Job not found")

        if status_code != 200:
            raise ExternalServiceError(f"ML service error: {payload}")
            
        if not isinstance(payload, dict):
            raise DataIntegrityError("ML service returned non-JSON payload")

        job = payload.get("job")
        if not isinstance(job, dict):
            raise DataIntegrityError("ML service job payload is missing")

        status = str(job.get("status"))
        if status != "done":
            raise ConflictError(f"Job is not ready yet. Current status: {status}")

        pdf_path_raw = (
            job.get("result_manifest", {})
            .get("tablature", {})
            .get("pdf")
        )
        if not pdf_path_raw:
            raise DataIntegrityError("PDF path missing in result manifest")

        pdf_path = Path(str(pdf_path_raw))
        if not pdf_path.exists():
            raise DataIntegrityError(f"PDF file not found: {pdf_path}")

        return PdfArtifact(
            file_path=pdf_path,
            download_filename=f"{job_id}.pdf",
        )

