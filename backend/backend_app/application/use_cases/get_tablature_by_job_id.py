from __future__ import annotations

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import ConflictError, DataIntegrityError, ExternalServiceError, NotFoundError
from backend_app.domain.models import TablatureArtifact


class GetTablatureByJobIdUseCase:
    def __init__(self, ml_service: MlServicePort) -> None:
        self.ml_service = ml_service

    async def execute(self, *, job_id: str) -> TablatureArtifact:
        status_code, payload = await self.ml_service.get_tablature(job_id=job_id)

        if status_code == 404:
            raise NotFoundError("Tablature or job not found")
        
        if status_code == 409:
            raise ConflictError("Job is not ready yet")
        
        if status_code != 200:
            raise ExternalServiceError(f"ML service error: {payload}")
        
        if not isinstance(payload, dict):
            raise DataIntegrityError("ML service returned non-JSON payload")

        tablature = payload.get("tablature")
        if not isinstance(tablature, dict):
            raise DataIntegrityError("Tablature payload is missing")

        return TablatureArtifact(job_id=job_id, tablature=tablature)

