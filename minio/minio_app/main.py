from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from minio_app.config import Settings, get_settings
from minio_app.storage import ObjectStorage


@lru_cache(maxsize=1)
def _build_storage() -> ObjectStorage:
    settings: Settings = get_settings()
    return ObjectStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
    )


app = FastAPI(title="minio-service", version="0.1.0")


@app.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict:
    try:
        storage = _build_storage()
        await storage.ensure_ready()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.put("/v1/objects/{object_key:path}")
async def put_object(object_key: str, request: Request) -> dict:
    payload = await request.body()
    content_type = str(request.headers.get("content-type") or "application/octet-stream")
    storage = _build_storage()
    try:
        key = await storage.put_bytes(object_key=object_key, data=payload, content_type=content_type)
        return {"object_key": key}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/objects/{object_key:path}")
async def get_object(object_key: str) -> Response:
    storage = _build_storage()
    try:
        payload, media_type = await storage.get_bytes(object_key=object_key)
        return Response(content=payload, media_type=media_type or "application/octet-stream")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Object not found")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
