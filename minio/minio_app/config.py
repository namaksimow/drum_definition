from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[1]
    load_dotenv(service_root / ".env")

    endpoint = str(os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")).strip()
    access_key = str(os.getenv("MINIO_ACCESS_KEY", "minioadmin")).strip()
    secret_key = str(os.getenv("MINIO_SECRET_KEY", "minioadmin")).strip()
    bucket = str(os.getenv("MINIO_BUCKET", "drum-media")).strip() or "drum-media"
    secure_raw = str(os.getenv("MINIO_SECURE", "false")).strip().lower()
    secure = secure_raw in {"1", "true", "yes", "on"}

    return Settings(
        app_host=str(os.getenv("MINIO_SERVICE_HOST", "0.0.0.0")).strip() or "0.0.0.0",
        app_port=int(os.getenv("MINIO_SERVICE_PORT", "8070")),
        minio_endpoint=endpoint,
        minio_access_key=access_key,
        minio_secret_key=secret_key,
        minio_bucket=bucket,
        minio_secure=secure,
    )
