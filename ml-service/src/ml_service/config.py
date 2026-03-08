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
    data_dir: Path
    songs_dir: Path
    worker_poll_timeout_sec: float
    database_url: str | None
    db_user_id: int
    db_user_email: str
    db_user_nickname: str
    db_user_password_hash: str
    db_user_role_title: str
    tablature_visibility_id: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[2]
    repo_root = service_root.parent
    load_dotenv(service_root / ".env")

    return Settings(
        app_host=os.getenv("ML_SERVICE_HOST", "0.0.0.0"),
        app_port=int(os.getenv("ML_SERVICE_PORT", "8000")),
        data_dir=Path(os.getenv("ML_SERVICE_DATA_DIR", str(service_root / "data"))),
        songs_dir=Path(os.getenv("ML_SERVICE_SONGS_DIR", str(repo_root / "songs"))),
        worker_poll_timeout_sec=float(os.getenv("ML_SERVICE_WORKER_POLL_SEC", "1.0")),
        database_url=os.getenv("DATABASE_URL"),
        db_user_id=int(os.getenv("ML_SERVICE_DB_USER_ID", "1")),
        db_user_email=os.getenv("ML_SERVICE_DB_USER_EMAIL", "ml-service@local"),
        db_user_nickname=os.getenv("ML_SERVICE_DB_USER_NICKNAME", "ML Service"),
        db_user_password_hash=os.getenv("ML_SERVICE_DB_USER_PASSWORD_HASH", "ml-service-placeholder-hash"),
        db_user_role_title=os.getenv("ML_SERVICE_DB_USER_ROLE_TITLE", "user"),
        tablature_visibility_id=int(os.getenv("ML_SERVICE_TAB_VISIBILITY_ID", "1")),
    )
