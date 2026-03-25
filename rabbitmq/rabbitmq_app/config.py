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
    rabbitmq_url: str
    rabbitmq_queue_name: str
    rabbitmq_prefetch_count: int
    rabbitmq_connect_timeout_sec: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[1]
    load_dotenv(service_root / ".env")

    rabbitmq_url = str(os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")).strip()
    queue_name = str(os.getenv("RABBITMQ_QUEUE_NAME", "ml.jobs")).strip() or "ml.jobs"

    return Settings(
        app_host=str(os.getenv("RABBITMQ_SERVICE_HOST", "0.0.0.0")).strip() or "0.0.0.0",
        app_port=int(os.getenv("RABBITMQ_SERVICE_PORT", "8090")),
        rabbitmq_url=rabbitmq_url,
        rabbitmq_queue_name=queue_name,
        rabbitmq_prefetch_count=max(int(os.getenv("RABBITMQ_PREFETCH_COUNT", "1")), 1),
        rabbitmq_connect_timeout_sec=float(os.getenv("RABBITMQ_CONNECT_TIMEOUT_SEC", "10.0")),
    )

