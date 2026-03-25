from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, MetaData, Table, Text, func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from ml_service.domain.models import Job, JobStatus
from ml_service.ports.job_repo import JobRepo


def _to_async_sqlalchemy_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + database_url.split("postgresql://", 1)[1]
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + database_url.split("postgresql+psycopg://", 1)[1]
    return database_url


def _to_iso(dt: datetime | None) -> str:
    if dt is None:
        return datetime.utcnow().isoformat()
    return dt.isoformat()


class PostgresJobRepo(JobRepo):
    def __init__(
        self,
        database_url: str,
        default_user_id: int = 1,
        default_user_email: str = "ml-service@local",
        default_user_nickname: str = "ML Service",
        default_user_password_hash: str = "ml-service-placeholder-hash",
        default_role_title: str = "user",
    ) -> None:
        self._database_url = _to_async_sqlalchemy_url(database_url)
        self._default_user_id = int(default_user_id)
        self._default_user_email = str(default_user_email)
        self._default_user_nickname = str(default_user_nickname)
        self._default_user_password_hash = str(default_user_password_hash)
        self._default_role_title = str(default_role_title)
        self._engine: AsyncEngine = create_async_engine(
            self._database_url,
            future=True,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        self._metadata = MetaData()
        self._roles_table = Table(
            "roles",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("role_title", Text, nullable=False),
        )
        self._users_table = Table(
            "users",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("email", Text, nullable=False),
            Column("nickname", Text, nullable=False),
            Column("password_hash", Text, nullable=False),
            Column("role_id", Integer, ForeignKey("roles.id"), nullable=False),
        )
        self._status_table = Table(
            "status",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("title", Text, nullable=False),
        )
        self._tracks_table = Table(
            "tracks",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("user_id", Integer, nullable=False),
            Column("file_name", Text, nullable=False),
            Column("file_path", Text, nullable=False),
            Column("duration", Integer, nullable=False),
        )
        self._task_table = Table(
            "task",
            self._metadata,
            Column("id", Integer, primary_key=True),
            Column("track_id", Integer, ForeignKey("tracks.id"), nullable=False),
            Column("status_id", Integer, ForeignKey("status.id"), nullable=False),
            Column("result_manifest", JSON, nullable=False),
            Column("error", Text, nullable=True),
            Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
            Column("started_at", DateTime(timezone=True), nullable=True),
            Column("finished_at", DateTime(timezone=True), nullable=True),
        )

    async def _get_status_id(self, session, status_title: JobStatus) -> int:
        result = await session.execute(
            select(self._status_table.c.id).where(self._status_table.c.title == status_title).limit(1)
        )
        status_id = result.scalar_one_or_none()
        if status_id is not None:
            return int(status_id)

        try:
            created_status = await session.execute(
                insert(self._status_table).values(title=status_title).returning(self._status_table.c.id)
            )
            return int(created_status.scalar_one())
        except IntegrityError:
            existing = await session.execute(
                select(self._status_table.c.id).where(self._status_table.c.title == status_title).limit(1)
            )
            status_id = existing.scalar_one_or_none()
            if status_id is None:
                raise RuntimeError(f"Не удалось получить status '{status_title}'")
        return int(status_id)

    async def _ensure_default_role(self, session) -> int:
        result = await session.execute(
            select(self._roles_table.c.id).where(self._roles_table.c.role_title == self._default_role_title).limit(1)
        )
        role_id = result.scalar_one_or_none()
        if role_id is not None:
            return int(role_id)

        created_role = await session.execute(
            insert(self._roles_table).values(role_title=self._default_role_title).returning(self._roles_table.c.id)
        )
        return int(created_role.scalar_one())

    async def _resolve_track_user_id(self, session, *, preferred_user_id: int | None = None) -> int:
        if preferred_user_id is not None:
            preferred = await session.execute(
                select(self._users_table.c.id).where(self._users_table.c.id == int(preferred_user_id)).limit(1)
            )
            preferred_id = preferred.scalar_one_or_none()
            if preferred_id is not None:
                return int(preferred_id)

        configured_user = await session.execute(
            select(self._users_table.c.id).where(self._users_table.c.id == self._default_user_id).limit(1)
        )
        configured_user_id = configured_user.scalar_one_or_none()
        if configured_user_id is not None:
            return int(configured_user_id)

        any_user = await session.execute(select(self._users_table.c.id).order_by(self._users_table.c.id.asc()).limit(1))
        any_user_id = any_user.scalar_one_or_none()
        if any_user_id is not None:
            return int(any_user_id)

        role_id = await self._ensure_default_role(session)
        user_values: dict[str, int | str] = {
            "email": self._default_user_email,
            "nickname": self._default_user_nickname,
            "password_hash": self._default_user_password_hash,
            "role_id": role_id,
        }
        if self._default_user_id > 0:
            user_values["id"] = self._default_user_id

        try:
            created_user = await session.execute(
                insert(self._users_table).values(**user_values).returning(self._users_table.c.id)
            )
            return int(created_user.scalar_one())
        except IntegrityError:
            # Another process could insert the same email in parallel.
            existing_by_email = await session.execute(
                select(self._users_table.c.id).where(self._users_table.c.email == self._default_user_email).limit(1)
            )
            email_user_id = existing_by_email.scalar_one_or_none()
            if email_user_id is not None:
                return int(email_user_id)

            fallback_user = await session.execute(
                select(self._users_table.c.id).order_by(self._users_table.c.id.asc()).limit(1)
            )
            fallback_user_id = fallback_user.scalar_one_or_none()
            if fallback_user_id is not None:
                return int(fallback_user_id)

            raise RuntimeError("Не удалось определить пользователя для записи track")

    async def create(
        self,
        job: Job,
        *,
        owner_user_id: int | None = None,
        track_title: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                queued_status_id = await self._get_status_id(session, "queued")
                track_user_id = await self._resolve_track_user_id(
                    session,
                    preferred_user_id=owner_user_id,
                )
                normalized_title = (track_title or "").strip()
                persisted_title = normalized_title if normalized_title else job.filename

                track_row = await session.execute(
                    insert(self._tracks_table)
                    .values(
                        user_id=track_user_id,
                        file_name=persisted_title,
                        file_path=job.input_key,
                        duration=0,
                    )
                    .returning(self._tracks_table.c.id)
                )
                track_id = int(track_row.scalar_one())

                task_row = await session.execute(
                    insert(self._task_table)
                    .values(
                        track_id=track_id,
                        status_id=queued_status_id,
                    )
                    .returning(
                        self._task_table.c.id,
                        self._task_table.c.created_at,
                    )
                )
                created = task_row.first()
                if created is None:
                    raise RuntimeError("Failed to create task row")

                # Important: public job_id = task.id from DB.
                job.id = str(created.id)
                job.status = "queued"
                job.created_at = _to_iso(created.created_at)
                job.updated_at = job.created_at

    async def get(self, job_id: str) -> Job | None:
        try:
            task_id = int(job_id)
        except ValueError:
            return None

        async with self._session_factory() as session:
            query = (
                select(
                    self._task_table.c.id,
                    self._task_table.c.created_at,
                    self._task_table.c.started_at,
                    self._task_table.c.finished_at,
                    self._task_table.c.result_manifest,
                    self._task_table.c.error,
                    self._status_table.c.title.label("status_title"),
                    self._tracks_table.c.file_name,
                    self._tracks_table.c.file_path,
                )
                .select_from(
                    self._task_table.join(self._status_table, self._status_table.c.id == self._task_table.c.status_id).join(
                        self._tracks_table, self._tracks_table.c.id == self._task_table.c.track_id
                    )
                )
                .where(self._task_table.c.id == task_id)
                .limit(1)
            )
            row = (await session.execute(query)).first()

        if row is None:
            return None

        status_title = str(row.status_title)
        if status_title not in {"queued", "processing", "done", "failed"}:
            status_title = "queued"

        updated_at_dt = row.finished_at or row.started_at or row.created_at
        return Job(
            id=str(row.id),
            filename=str(row.file_name),
            input_key=str(row.file_path),
            status=status_title,  # type: ignore[arg-type]
            created_at=_to_iso(row.created_at),
            updated_at=_to_iso(updated_at_dt),
            result_manifest=dict(row.result_manifest or {}),
            error=str(row.error) if row.error is not None else None,
        )

    async def list(self) -> list[Job]:
        async with self._session_factory() as session:
            query = (
                select(
                    self._task_table.c.id,
                    self._task_table.c.created_at,
                    self._task_table.c.started_at,
                    self._task_table.c.finished_at,
                    self._task_table.c.result_manifest,
                    self._task_table.c.error,
                    self._status_table.c.title.label("status_title"),
                    self._tracks_table.c.file_name,
                    self._tracks_table.c.file_path,
                )
                .select_from(
                    self._task_table.join(self._status_table, self._status_table.c.id == self._task_table.c.status_id).join(
                        self._tracks_table, self._tracks_table.c.id == self._task_table.c.track_id
                    )
                )
                .order_by(self._task_table.c.id.desc())
            )
            rows = (await session.execute(query)).all()

        jobs: list[Job] = []
        for row in rows:
            status_title = str(row.status_title)
            if status_title not in {"queued", "processing", "done", "failed"}:
                status_title = "queued"
            updated_at_dt = row.finished_at or row.started_at or row.created_at
            jobs.append(
                Job(
                    id=str(row.id),
                    filename=str(row.file_name),
                    input_key=str(row.file_path),
                    status=status_title,  # type: ignore[arg-type]
                    created_at=_to_iso(row.created_at),
                    updated_at=_to_iso(updated_at_dt),
                    result_manifest=dict(row.result_manifest or {}),
                    error=str(row.error) if row.error is not None else None,
                )
            )
        return jobs

    async def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        result_manifest: dict | None = None,
        error: str | None = None,
    ) -> Job | None:
        try:
            task_id = int(job_id)
        except ValueError:
            return None

        async with self._session_factory() as session:
            async with session.begin():
                values: dict = {}
                if status is not None:
                    values["status_id"] = await self._get_status_id(session, status)
                    if status == "processing":
                        values["started_at"] = func.now()
                    if status in {"done", "failed"}:
                        values["finished_at"] = func.now()
                values["error"] = error

                if values:
                    await session.execute(
                        update(self._task_table).where(self._task_table.c.id == task_id).values(**values)
                    )
                if result_manifest is not None:
                    await session.execute(
                        update(self._task_table)
                        .where(self._task_table.c.id == task_id)
                        .values(result_manifest=result_manifest)
                    )
        return await self.get(job_id)
