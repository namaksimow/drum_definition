from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_host: str
    app_port: int
    data_dir: Path
    songs_dir: Path
    worker_poll_timeout_sec: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[2]
    repo_root = service_root.parent

    return Settings(
        app_host=os.getenv("ML_SERVICE_HOST", "0.0.0.0"),
        app_port=int(os.getenv("ML_SERVICE_PORT", "8000")),
        data_dir=Path(os.getenv("ML_SERVICE_DATA_DIR", str(service_root / "data"))),
        songs_dir=Path(os.getenv("ML_SERVICE_SONGS_DIR", str(repo_root / "songs"))),
        worker_poll_timeout_sec=float(os.getenv("ML_SERVICE_WORKER_POLL_SEC", "1.0")),
    )
