from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from backend_app.adapters.frontend_filesystem import FrontendFilesystemAdapter
from backend_app.adapters.ml_service_http import MlServiceHttpAdapter
from backend_app.adapters.postgres_service_http import PostgresServiceHttpAdapter
from backend_app.application.use_cases.download_public_tablature_json import DownloadPublicTablatureJsonUseCase
from backend_app.application.use_cases.create_public_tablature_comment import CreatePublicTablatureCommentUseCase
from backend_app.application.use_cases.get_current_user import GetCurrentUserUseCase
from backend_app.application.use_cases.get_index_page import GetIndexPageUseCase
from backend_app.application.use_cases.get_job_by_id import GetJobByIdUseCase
from backend_app.application.use_cases.get_public_tablature_by_id import GetPublicTablatureByIdUseCase
from backend_app.application.use_cases.get_public_tablature_reactions import GetPublicTablatureReactionsUseCase
from backend_app.application.use_cases.get_personal_tablature_by_id import GetPersonalTablatureByIdUseCase
from backend_app.application.use_cases.get_pdf_by_job_id import GetPdfByJobIdUseCase
from backend_app.application.use_cases.get_tablature_by_job_id import GetTablatureByJobIdUseCase
from backend_app.application.use_cases.login_user import LoginUserUseCase
from backend_app.application.use_cases.list_public_tablature_comments import ListPublicTablatureCommentsUseCase
from backend_app.application.use_cases.list_public_tablatures import ListPublicTablaturesUseCase
from backend_app.application.use_cases.list_personal_tablatures import ListPersonalTablaturesUseCase
from backend_app.application.use_cases.register_user import RegisterUserUseCase
from backend_app.application.use_cases.set_public_tablature_reaction import SetPublicTablatureReactionUseCase
from backend_app.application.use_cases.update_current_user import UpdateCurrentUserUseCase
from backend_app.application.use_cases.update_personal_tablature import UpdatePersonalTablatureUseCase
from backend_app.application.use_cases.upload_audio import UploadAudioUseCase
from backend_app.config import Settings, get_settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    get_index_page: GetIndexPageUseCase
    upload_audio: UploadAudioUseCase
    get_job_by_id: GetJobByIdUseCase
    get_pdf_by_job_id: GetPdfByJobIdUseCase
    get_tablature_by_job_id: GetTablatureByJobIdUseCase
    list_public_tablatures: ListPublicTablaturesUseCase
    list_public_tablature_comments: ListPublicTablatureCommentsUseCase
    create_public_tablature_comment: CreatePublicTablatureCommentUseCase
    get_public_tablature_reactions: GetPublicTablatureReactionsUseCase
    set_public_tablature_reaction: SetPublicTablatureReactionUseCase
    list_personal_tablatures: ListPersonalTablaturesUseCase
    get_personal_tablature_by_id: GetPersonalTablatureByIdUseCase
    get_public_tablature_by_id: GetPublicTablatureByIdUseCase
    update_personal_tablature: UpdatePersonalTablatureUseCase
    download_public_tablature_json: DownloadPublicTablatureJsonUseCase
    register_user: RegisterUserUseCase
    login_user: LoginUserUseCase
    get_current_user: GetCurrentUserUseCase
    update_current_user: UpdateCurrentUserUseCase
    frontend_assets_dir: str


@lru_cache(maxsize=1)
def get_container() -> Container:
    settings = get_settings()

    frontend_adapter = FrontendFilesystemAdapter(settings.frontend_dir)
    ml_adapter = MlServiceHttpAdapter(
        base_url=settings.ml_service_url,
        timeout_sec=settings.ml_service_timeout_sec,
    )
    postgres_adapter = PostgresServiceHttpAdapter(
        base_url=settings.postgres_service_url,
        timeout_sec=settings.ml_service_timeout_sec,
    )

    return Container(
        settings=settings,
        get_index_page=GetIndexPageUseCase(frontend=frontend_adapter),
        upload_audio=UploadAudioUseCase(ml_service=ml_adapter),
        get_job_by_id=GetJobByIdUseCase(ml_service=ml_adapter),
        get_pdf_by_job_id=GetPdfByJobIdUseCase(ml_service=ml_adapter),
        get_tablature_by_job_id=GetTablatureByJobIdUseCase(ml_service=ml_adapter),
        list_public_tablatures=ListPublicTablaturesUseCase(postgres_service=postgres_adapter),
        list_public_tablature_comments=ListPublicTablatureCommentsUseCase(postgres_service=postgres_adapter),
        create_public_tablature_comment=CreatePublicTablatureCommentUseCase(postgres_service=postgres_adapter),
        get_public_tablature_reactions=GetPublicTablatureReactionsUseCase(postgres_service=postgres_adapter),
        set_public_tablature_reaction=SetPublicTablatureReactionUseCase(postgres_service=postgres_adapter),
        list_personal_tablatures=ListPersonalTablaturesUseCase(postgres_service=postgres_adapter),
        get_personal_tablature_by_id=GetPersonalTablatureByIdUseCase(postgres_service=postgres_adapter),
        get_public_tablature_by_id=GetPublicTablatureByIdUseCase(postgres_service=postgres_adapter),
        update_personal_tablature=UpdatePersonalTablatureUseCase(postgres_service=postgres_adapter),
        download_public_tablature_json=DownloadPublicTablatureJsonUseCase(postgres_service=postgres_adapter),
        register_user=RegisterUserUseCase(postgres_service=postgres_adapter),
        login_user=LoginUserUseCase(postgres_service=postgres_adapter),
        get_current_user=GetCurrentUserUseCase(postgres_service=postgres_adapter),
        update_current_user=UpdateCurrentUserUseCase(postgres_service=postgres_adapter),
        frontend_assets_dir=str(frontend_adapter.assets_dir()),
    )
