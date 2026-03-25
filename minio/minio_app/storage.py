from __future__ import annotations

import asyncio
from io import BytesIO

from minio import Minio
from minio.error import S3Error


class ObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
    ) -> None:
        self.bucket = bucket.strip()
        self._client = Minio(
            endpoint.strip(),
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket_ready = False
        self._bucket_lock = asyncio.Lock()

    async def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        async with self._bucket_lock:
            if self._bucket_ready:
                return
            exists = await _run_blocking(self._client.bucket_exists, self.bucket)
            if not exists:
                await _run_blocking(self._client.make_bucket, self.bucket)
            self._bucket_ready = True

    async def ensure_ready(self) -> None:
        await self._ensure_bucket()

    async def put_bytes(self, *, object_key: str, data: bytes, content_type: str) -> str:
        key = object_key.strip().lstrip("/")
        if not key:
            raise ValueError("Object key is required")
        if not data:
            raise ValueError("Data is empty")

        await self._ensure_bucket()
        stream = BytesIO(data)
        await _run_blocking(
            self._client.put_object,
            self.bucket,
            key,
            stream,
            len(data),
            content_type=content_type or "application/octet-stream",
        )
        return key

    async def get_bytes(self, *, object_key: str) -> tuple[bytes, str]:
        key = object_key.strip().lstrip("/")
        if not key:
            raise FileNotFoundError("Object key is empty")

        await self._ensure_bucket()
        try:
            response = await _run_blocking(self._client.get_object, self.bucket, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                raise FileNotFoundError(f"Object not found: {key}") from exc
            raise

        def _read() -> tuple[bytes, str]:
            try:
                content = response.read()
                media_type = str(response.headers.get("Content-Type") or "application/octet-stream")
                return content, media_type
            finally:
                response.close()
                response.release_conn()

        return await _run_blocking(_read)


async def _run_blocking(func, /, *args, **kwargs):
    to_thread = getattr(asyncio, "to_thread", None)
    if to_thread is not None:
        return await to_thread(func, *args, **kwargs)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
