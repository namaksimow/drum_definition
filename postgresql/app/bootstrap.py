from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.adapters.postgres.sqlalchemy_gateway import AsyncSqlAlchemyDatabaseGateway, build_async_engine
from app.application.use_cases.check_db_health import CheckDbHealthUseCase
from app.application.use_cases.add_public_tablature_comment import AddPublicTablatureCommentUseCase
from app.application.use_cases.get_current_user import GetCurrentUserUseCase
from app.application.use_cases.get_public_tablature import GetPublicTablatureUseCase
from app.application.use_cases.get_public_tablature_reactions import GetPublicTablatureReactionsUseCase
from app.application.use_cases.get_user_tablature import GetUserTablatureUseCase
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.list_public_tablature_comments import ListPublicTablatureCommentsUseCase
from app.application.use_cases.list_public_tablatures import ListPublicTablaturesUseCase
from app.application.use_cases.list_tables import ListTablesUseCase
from app.application.use_cases.list_user_tablatures import ListUserTablaturesUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.application.use_cases.set_public_tablature_reaction import SetPublicTablatureReactionUseCase
from app.application.use_cases.update_current_user_nickname import UpdateCurrentUserNicknameUseCase
from app.application.use_cases.update_user_tablature import UpdateUserTablatureUseCase
from app.config import Settings, get_settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    check_db_health: CheckDbHealthUseCase
    list_tables: ListTablesUseCase
    list_public_tablatures: ListPublicTablaturesUseCase
    get_public_tablature: GetPublicTablatureUseCase
    list_public_tablature_comments: ListPublicTablatureCommentsUseCase
    add_public_tablature_comment: AddPublicTablatureCommentUseCase
    get_public_tablature_reactions: GetPublicTablatureReactionsUseCase
    set_public_tablature_reaction: SetPublicTablatureReactionUseCase
    list_user_tablatures: ListUserTablaturesUseCase
    get_user_tablature: GetUserTablatureUseCase
    update_user_tablature: UpdateUserTablatureUseCase
    register_user: RegisterUserUseCase
    login_user: LoginUserUseCase
    get_current_user: GetCurrentUserUseCase
    update_current_user_nickname: UpdateCurrentUserNicknameUseCase


@lru_cache(maxsize=1)
def get_container() -> Container:
    settings = get_settings()
    engine = build_async_engine(settings.database_url)
    gateway = AsyncSqlAlchemyDatabaseGateway(engine)

    return Container(
        settings=settings,
        check_db_health=CheckDbHealthUseCase(gateway),
        list_tables=ListTablesUseCase(gateway),
        list_public_tablatures=ListPublicTablaturesUseCase(gateway),
        get_public_tablature=GetPublicTablatureUseCase(gateway),
        list_public_tablature_comments=ListPublicTablatureCommentsUseCase(gateway),
        add_public_tablature_comment=AddPublicTablatureCommentUseCase(gateway),
        get_public_tablature_reactions=GetPublicTablatureReactionsUseCase(gateway),
        set_public_tablature_reaction=SetPublicTablatureReactionUseCase(gateway),
        list_user_tablatures=ListUserTablaturesUseCase(gateway),
        get_user_tablature=GetUserTablatureUseCase(gateway),
        update_user_tablature=UpdateUserTablatureUseCase(gateway),
        register_user=RegisterUserUseCase(gateway),
        login_user=LoginUserUseCase(
            gateway,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm,
            jwt_expire_minutes=settings.jwt_expire_minutes,
        ),
        get_current_user=GetCurrentUserUseCase(
            gateway,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm,
        ),
        update_current_user_nickname=UpdateCurrentUserNicknameUseCase(
            gateway,
            jwt_secret_key=settings.jwt_secret_key,
            jwt_algorithm=settings.jwt_algorithm,
        ),
    )
