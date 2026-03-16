from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.adapters.postgres.sqlalchemy_gateway import AsyncSqlAlchemyDatabaseGateway, build_async_engine
from app.application.use_cases.check_db_health import CheckDbHealthUseCase
from app.application.use_cases.add_public_tablature_comment import AddPublicTablatureCommentUseCase
from app.application.use_cases.create_author_role_request import CreateAuthorRoleRequestUseCase
from app.application.use_cases.create_user_course_lesson import CreateUserCourseLessonUseCase
from app.application.use_cases.create_course import CreateCourseUseCase
from app.application.use_cases.delete_user_course_lesson import DeleteUserCourseLessonUseCase
from app.application.use_cases.delete_user_course import DeleteUserCourseUseCase
from app.application.use_cases.get_author_course_statistics import GetAuthorCourseStatisticsUseCase
from app.application.use_cases.get_current_user import GetCurrentUserUseCase
from app.application.use_cases.get_latest_author_role_request import GetLatestAuthorRoleRequestUseCase
from app.application.use_cases.get_public_tablature import GetPublicTablatureUseCase
from app.application.use_cases.get_public_tablature_reactions import GetPublicTablatureReactionsUseCase
from app.application.use_cases.get_user_tablature import GetUserTablatureUseCase
from app.application.use_cases.login_user import LoginUserUseCase
from app.application.use_cases.list_public_course_lessons import ListPublicCourseLessonsUseCase
from app.application.use_cases.list_public_courses import ListPublicCoursesUseCase
from app.application.use_cases.list_public_tablature_comments import ListPublicTablatureCommentsUseCase
from app.application.use_cases.list_public_tablatures import ListPublicTablaturesUseCase
from app.application.use_cases.list_author_role_requests import ListAuthorRoleRequestsUseCase
from app.application.use_cases.list_user_course_lesson_progress import ListUserCourseLessonProgressUseCase
from app.application.use_cases.list_user_course_lessons import ListUserCourseLessonsUseCase
from app.application.use_cases.list_user_courses import ListUserCoursesUseCase
from app.application.use_cases.list_tables import ListTablesUseCase
from app.application.use_cases.list_user_tablatures import ListUserTablaturesUseCase
from app.application.use_cases.register_user import RegisterUserUseCase
from app.application.use_cases.set_user_course_lesson_progress import SetUserCourseLessonProgressUseCase
from app.application.use_cases.set_public_tablature_reaction import SetPublicTablatureReactionUseCase
from app.application.use_cases.track_user_course_visit import TrackUserCourseVisitUseCase
from app.application.use_cases.update_current_user_nickname import UpdateCurrentUserNicknameUseCase
from app.application.use_cases.update_author_role_request_status import UpdateAuthorRoleRequestStatusUseCase
from app.application.use_cases.update_user_course_lesson import UpdateUserCourseLessonUseCase
from app.application.use_cases.update_user_course import UpdateUserCourseUseCase
from app.application.use_cases.update_user_tablature import UpdateUserTablatureUseCase
from app.config import Settings, get_settings


@dataclass(frozen=True)
class Container:
    settings: Settings
    check_db_health: CheckDbHealthUseCase
    list_tables: ListTablesUseCase
    list_public_tablatures: ListPublicTablaturesUseCase
    list_public_courses: ListPublicCoursesUseCase
    list_public_course_lessons: ListPublicCourseLessonsUseCase
    create_course: CreateCourseUseCase
    list_user_courses: ListUserCoursesUseCase
    list_user_course_lessons: ListUserCourseLessonsUseCase
    list_user_course_lesson_progress: ListUserCourseLessonProgressUseCase
    set_user_course_lesson_progress: SetUserCourseLessonProgressUseCase
    track_user_course_visit: TrackUserCourseVisitUseCase
    get_author_course_statistics: GetAuthorCourseStatisticsUseCase
    create_user_course_lesson: CreateUserCourseLessonUseCase
    update_user_course_lesson: UpdateUserCourseLessonUseCase
    delete_user_course_lesson: DeleteUserCourseLessonUseCase
    update_user_course: UpdateUserCourseUseCase
    delete_user_course: DeleteUserCourseUseCase
    get_latest_author_role_request: GetLatestAuthorRoleRequestUseCase
    create_author_role_request: CreateAuthorRoleRequestUseCase
    list_author_role_requests: ListAuthorRoleRequestsUseCase
    update_author_role_request_status: UpdateAuthorRoleRequestStatusUseCase
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
        list_public_courses=ListPublicCoursesUseCase(gateway),
        list_public_course_lessons=ListPublicCourseLessonsUseCase(gateway),
        create_course=CreateCourseUseCase(gateway),
        list_user_courses=ListUserCoursesUseCase(gateway),
        list_user_course_lessons=ListUserCourseLessonsUseCase(gateway),
        list_user_course_lesson_progress=ListUserCourseLessonProgressUseCase(gateway),
        set_user_course_lesson_progress=SetUserCourseLessonProgressUseCase(gateway),
        track_user_course_visit=TrackUserCourseVisitUseCase(gateway),
        get_author_course_statistics=GetAuthorCourseStatisticsUseCase(gateway),
        create_user_course_lesson=CreateUserCourseLessonUseCase(gateway),
        update_user_course_lesson=UpdateUserCourseLessonUseCase(gateway),
        delete_user_course_lesson=DeleteUserCourseLessonUseCase(gateway),
        update_user_course=UpdateUserCourseUseCase(gateway),
        delete_user_course=DeleteUserCourseUseCase(gateway),
        get_latest_author_role_request=GetLatestAuthorRoleRequestUseCase(gateway),
        create_author_role_request=CreateAuthorRoleRequestUseCase(gateway),
        list_author_role_requests=ListAuthorRoleRequestsUseCase(gateway),
        update_author_role_request_status=UpdateAuthorRoleRequestStatusUseCase(gateway),
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
