from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.adapters.postgres.sqlalchemy_gateway import AsyncSqlAlchemyDatabaseGateway, build_async_engine
from app.application.use_cases.check_db_health import CheckDbHealthUseCase
from app.application.use_cases.list_tables import ListTablesUseCase
from app.config import Settings, get_settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    check_db_health: CheckDbHealthUseCase
    list_tables: ListTablesUseCase


@lru_cache(maxsize=1)
def get_container() -> Container:
    settings = get_settings()
    engine = build_async_engine(settings.database_url)
    gateway = AsyncSqlAlchemyDatabaseGateway(engine)

    return Container(
        settings=settings,
        check_db_health=CheckDbHealthUseCase(gateway),
        list_tables=ListTablesUseCase(gateway),
    )
