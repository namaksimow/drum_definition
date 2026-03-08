from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, Table, Text, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from ml_service.ports.tablature_store import TablatureStore


def _to_async_sqlalchemy_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + database_url.split("postgresql://", 1)[1]
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + database_url.split("postgresql+psycopg://", 1)[1]
    return database_url


class PostgresTablatureStore(TablatureStore):
    def __init__(self, database_url: str, default_visibility_id: int = 1) -> None:
        self._database_url = _to_async_sqlalchemy_url(database_url)
        self._default_visibility_id = int(default_visibility_id)
        self._engine: AsyncEngine = create_async_engine(
            self._database_url,
            future=True,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        self._metadata = MetaData()
        self._table = Table(
            "tablatures",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("task_id", Integer, nullable=False),
            Column("visibility_id", Integer, nullable=False),
            Column("json_format", JSON, nullable=False),
            Column("result_path", Text, nullable=True),
            Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
            Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        )

    async def save(self, job_id: str, tablature: dict) -> None:
        try:
            task_id = int(job_id)
        except ValueError:
            raise RuntimeError(f"job_id '{job_id}' is not numeric task id")

        async with self._session_factory() as session:
            async with session.begin():
                existing = await session.execute(
                    select(self._table.c.id).where(self._table.c.task_id == task_id).order_by(self._table.c.id.desc()).limit(1)
                )
                row = existing.first()
                if row is None:
                    await session.execute(
                        insert(self._table).values(
                            task_id=task_id,
                            visibility_id=self._default_visibility_id,
                            json_format=tablature,
                        )
                    )
                else:
                    await session.execute(
                        update(self._table)
                        .where(self._table.c.id == row.id)
                        .values(
                            json_format=tablature,
                            updated_at=text("now()"),
                        )
                    )

    async def get(self, job_id: str) -> dict | None:
        try:
            task_id = int(job_id)
        except ValueError:
            return None

        async with self._session_factory() as session:
            result = await session.execute(
                select(self._table.c.json_format)
                .where(self._table.c.task_id == task_id)
                .order_by(self._table.c.id.desc())
                .limit(1)
            )
            row = result.first()
        if row is None:
            return None

        payload = row[0]
        if payload is None:
            return None
        if isinstance(payload, dict):
            return payload
        return dict(payload)
