from __future__ import annotations

import httpx

from backend_app.application.ports.ml_service_port import MlServicePort
from backend_app.domain.errors import ExternalServiceError


class MlServiceHttpAdapter(MlServicePort):
    def __init__(self, base_url: str, timeout_sec: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    async def submit_upload(
        self,
        *,
        filename: str,
        data: bytes,
        content_type: str,
        user_id: int | None = None,
        tablature_name: str | None = None,
    ) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                files = {"file": (filename, data, content_type)}
                form_data: dict[str, str] = {}
                if user_id is not None:
                    form_data["user_id"] = str(user_id)
                if tablature_name:
                    form_data["tablature_name"] = str(tablature_name)
                payload = form_data if form_data else None
                resp = await client.post(f"{self.base_url}/v1/jobs", files=files, data=payload)
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

    async def get_tablature(self, *, job_id: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/v1/jobs/{job_id}/tablature")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"ML service get-tablature request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_pdf(self, *, job_id: str) -> tuple[int, bytes | dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/v1/jobs/{job_id}/pdf")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"ML service get-pdf request failed: {exc}") from exc

        if resp.status_code == 200:
            return resp.status_code, resp.content

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload
