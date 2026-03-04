from __future__ import annotations

from dataclasses import dataclass

from ml_service.adapters.mock.mock_job_repo import MockJobRepo
from ml_service.adapters.mock.mock_queue import MockQueue
from ml_service.adapters.mock.mock_storage import MockFileStorage
from ml_service.config import Settings, get_settings
from ml_service.services.job_service import JobService


@dataclass
class Container:
    settings: Settings
    job_repo: MockJobRepo
    file_storage: MockFileStorage
    job_queue: MockQueue
    job_service: JobService


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is not None:
        return _container

    settings = get_settings()
    job_repo = MockJobRepo()
    file_storage = MockFileStorage(base_dir=settings.data_dir)
    job_queue = MockQueue()
    job_service = JobService(repo=job_repo, storage=file_storage, queue=job_queue)

    _container = Container(
        settings=settings,
        job_repo=job_repo,
        file_storage=file_storage,
        job_queue=job_queue,
        job_service=job_service,
    )

    return _container