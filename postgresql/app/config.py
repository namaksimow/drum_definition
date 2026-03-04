from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/drum_definition"
    app_host: str = "0.0.0.0"
    app_port: int = 8090


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
