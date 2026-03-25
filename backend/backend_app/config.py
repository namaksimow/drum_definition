from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ml_service_url: str
    postgres_service_url: str
    ml_service_timeout_sec: float
    frontend_dir: Path
    minio_service_url: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent

    minio_service_url = os.getenv("MINIO_SERVICE_URL", "http://127.0.0.1:8070")
    
    return Settings(
        ml_service_url=os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000"),
        postgres_service_url=os.getenv("POSTGRES_SERVICE_URL", "http://127.0.0.1:8090"),
        ml_service_timeout_sec=float(os.getenv("BACKEND_HTTP_TIMEOUT_SEC", "120.0")),
        frontend_dir=repo_root / "frontend",
        minio_service_url=minio_service_url.strip() if minio_service_url and minio_service_url.strip() else None,
    )
