from __future__ import annotations

import httpx

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import ExternalServiceError


class MlServiceHttpAdapter(MlServicePort):
    def __init__(self, base_url: str, timeout_sec: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    async def submit_upload(self, *, filename: str, data: bytes, content_type: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                files = {"file": (filename, data, content_type)}
                resp = await client.post(f"{self.base_url}/v1/jobs", files=files)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"ML service upload request failed: {exc}") from exc

        if resp.status_code != 200:
            raise ExternalServiceError(f"ML service upload error: {resp.text}")

        payload = resp.json()
        if not isinstance(payload, dict):
            raise ExternalServiceError("ML service returned invalid upload payload")
        return payload

    async def get_job(self, *, job_id: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/v1/jobs/{job_id}")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"ML service get-job request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

