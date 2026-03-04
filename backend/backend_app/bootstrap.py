from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from backend_app.adapters.frontend_filesystem import FrontendFilesystemAdapter
from backend_app.adapters.ml_service_http import MlServiceHttpAdapter
from backend_app.application.use_cases.get_index_page import GetIndexPageUseCase
from backend_app.application.use_cases.get_pdf_by_job_id import GetPdfByJobIdUseCase
from backend_app.application.use_cases.upload_audio import UploadAudioUseCase
from backend_app.config import Settings, get_settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    get_index_page: GetIndexPageUseCase
    upload_audio: UploadAudioUseCase
    get_pdf_by_job_id: GetPdfByJobIdUseCase
    frontend_assets_dir: str


@lru_cache(maxsize=1)
def get_container() -> Container:
    settings = get_settings()

    frontend_adapter = FrontendFilesystemAdapter(settings.frontend_dir)
    ml_adapter = MlServiceHttpAdapter(
        base_url=settings.ml_service_url,
        timeout_sec=settings.ml_service_timeout_sec,
    )

    return Container(
        settings=settings,
        get_index_page=GetIndexPageUseCase(frontend=frontend_adapter),
        upload_audio=UploadAudioUseCase(ml_service=ml_adapter),
        get_pdf_by_job_id=GetPdfByJobIdUseCase(ml_service=ml_adapter),
        frontend_assets_dir=str(frontend_adapter.assets_dir()),
    )

