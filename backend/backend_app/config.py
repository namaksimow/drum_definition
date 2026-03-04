from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ml_service_url: str
    ml_service_timeout_sec: float
    frontend_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent
    
    return Settings(
        ml_service_url=os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8000"),
        ml_service_timeout_sec=float(os.getenv("BACKEND_HTTP_TIMEOUT_SEC", "120.0")),
        frontend_dir=repo_root / "frontend",
    )

