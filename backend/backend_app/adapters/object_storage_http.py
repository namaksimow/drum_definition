from __future__ import annotations

import httpx

from backend_app.domain.errors import ExternalServiceError


class ObjectStorageHttpAdapter:
    def __init__(self, *, base_url: str, timeout_sec: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    async def upload_bytes(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        key = object_key.strip().lstrip("/")
        if not key:
            raise ValueError("Object key is required")
        if not data:
            raise ValueError("Data is empty")

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.put(
                    f"{self.base_url}/v1/objects/{key}",
                    content=data,
                    headers={"Content-Type": content_type or "application/octet-stream"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Object storage upload failed: {exc}") from exc

        if resp.status_code == 200:
            payload = resp.json()
            returned_key = payload.get("object_key")
            return str(returned_key or key)

        detail = resp.text
        raise ExternalServiceError(f"Object storage upload failed: {detail}")

    async def get_bytes(self, *, object_key: str) -> tuple[bytes, str]:
        key = object_key.strip().lstrip("/")
        if not key:
            raise FileNotFoundError("Object key is empty")

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/v1/objects/{key}")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Object storage get failed: {exc}") from exc

        if resp.status_code == 200:
            media_type = str(resp.headers.get("Content-Type") or "application/octet-stream")
            return resp.content, media_type
        if resp.status_code == 404:
            raise FileNotFoundError(f"Object not found: {key}")

        raise ExternalServiceError(f"Object storage get failed: {resp.text}")
