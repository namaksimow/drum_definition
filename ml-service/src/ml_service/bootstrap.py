from __future__ import annotations

from dataclasses import dataclass

from ml_service.adapters.mock.mock_queue import MockQueue
from ml_service.adapters.mock.mock_storage import MockFileStorage
from ml_service.adapters.postgres.postgres_job_repo import PostgresJobRepo
from ml_service.adapters.postgres.postgres_tablature_store import PostgresTablatureStore
from ml_service.config import Settings, get_settings
from ml_service.ports.job_repo import JobRepo
from ml_service.ports.tablature_store import TablatureStore
from ml_service.services.job_service import JobService


@dataclass
class Container:
    settings: Settings
    job_repo: JobRepo
    file_storage: MockFileStorage
    job_queue: MockQueue
    tablature_store: TablatureStore
    job_service: JobService


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is not None:
        return _container

    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is required. "
            "Mock repository отключен."
        )

    job_repo = PostgresJobRepo(
        settings.database_url,
        default_user_id=settings.db_user_id,
        default_user_email=settings.db_user_email,
        default_user_nickname=settings.db_user_nickname,
        default_user_password_hash=settings.db_user_password_hash,
        default_role_title=settings.db_user_role_title,
    )
    file_storage = MockFileStorage(base_dir=settings.data_dir)
    job_queue = MockQueue()
    tablature_store: TablatureStore = PostgresTablatureStore(
        settings.database_url,
        default_visibility_id=settings.tablature_visibility_id,
    )

    job_service = JobService(
        repo=job_repo,
        storage=file_storage,
        queue=job_queue,
        tablature_store=tablature_store,
    )

    _container = Container(
        settings=settings,
        job_repo=job_repo,
        file_storage=file_storage,
        job_queue=job_queue,
        tablature_store=tablature_store,
        job_service=job_service,
    )

    return _container
