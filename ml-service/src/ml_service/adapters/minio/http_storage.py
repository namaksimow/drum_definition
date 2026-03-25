from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path

import httpx

from ml_service.ports.file_storage import FileStorage


def _sanitize_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


class MinioHttpFileStorage(FileStorage):
    def __init__(
        self,
        *,
        base_url: str,
        base_dir: str | Path = "data",
        timeout_sec: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = float(timeout_sec)
        self.base_dir = Path(base_dir)
        self.cache_dir = self.base_dir / "minio-cache"
        self.results_dir = self.base_dir / "results"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, job_id: str, filename: str, data: bytes) -> str:
        safe_name = _sanitize_filename(filename)
        object_key = f"uploads/{job_id}/{safe_name}"
        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.put(
                f"{self.base_url}/v1/objects/{object_key}",
                content=data,
                headers={"Content-Type": content_type},
            )
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to upload to object storage: {resp.text}")
        return object_key

    async def resolve_input_path(self, input_key: str) -> Path:
        object_key = input_key.strip().lstrip("/")
        if not object_key:
            raise FileNotFoundError("Upload key is empty")

        cache_path = self.cache_dir / object_key
        if cache_path.exists():
            return cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.get(f"{self.base_url}/v1/objects/{object_key}")
        if resp.status_code == 404:
            raise FileNotFoundError(f"Upload not found for key: {object_key}")
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download from object storage: {resp.text}")

        await _run_blocking(cache_path.write_bytes, resp.content)
        return cache_path

    async def prepare_results_dir(self, job_id: str) -> Path:
        path = self.results_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path


async def _run_blocking(func, /, *args, **kwargs):
    to_thread = getattr(asyncio, "to_thread", None)
    if to_thread is not None:
        return await to_thread(func, *args, **kwargs)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
