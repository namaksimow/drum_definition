from __future__ import annotations

import asyncio

import pytest

from backend_app.application.use_cases.create_personal_course_lesson import CreatePersonalCourseLessonUseCase
from backend_app.application.use_cases.get_personal_course_statistics import GetPersonalCourseStatisticsUseCase
from backend_app.application.use_cases.list_admin_author_role_requests import ListAdminAuthorRoleRequestsUseCase
from backend_app.application.use_cases.list_admin_course_lessons import ListAdminCourseLessonsUseCase
from backend_app.application.use_cases.list_admin_courses import ListAdminCoursesUseCase
from backend_app.application.use_cases.list_admin_tablature_comments import ListAdminTablatureCommentsUseCase
from backend_app.application.use_cases.list_admin_tablatures import ListAdminTablaturesUseCase
from backend_app.application.use_cases.list_admin_users import ListAdminUsersUseCase
from backend_app.application.use_cases.list_personal_course_lesson_progress import (
    ListPersonalCourseLessonProgressUseCase,
)
from backend_app.application.use_cases.list_personal_course_lessons import ListPersonalCourseLessonsUseCase
from backend_app.application.use_cases.list_personal_courses import ListPersonalCoursesUseCase
from backend_app.application.use_cases.set_personal_course_lesson_progress import (
    SetPersonalCourseLessonProgressUseCase,
)
from backend_app.application.use_cases.track_personal_course_visit import TrackPersonalCourseVisitUseCase
from backend_app.application.use_cases.update_admin_author_role_request import (
    UpdateAdminAuthorRoleRequestUseCase,
)
from backend_app.application.use_cases.update_admin_course_visibility import (
    UpdateAdminCourseVisibilityUseCase,
)
from backend_app.application.use_cases.update_admin_tablature_visibility import (
    UpdateAdminTablatureVisibilityUseCase,
)
from backend_app.application.use_cases.update_admin_user_account import UpdateAdminUserAccountUseCase
from backend_app.application.use_cases.update_personal_course import UpdatePersonalCourseUseCase
from backend_app.application.use_cases.update_personal_course_lesson import (
    UpdatePersonalCourseLessonUseCase,
)
from backend_app.application.use_cases.update_personal_tablature import UpdatePersonalTablatureUseCase
from backend_app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DataIntegrityError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


def _run(coro):
    return asyncio.run(coro)


def _make_port(method_name: str, result: tuple[int, object]):
    class _Port:
        pass

    port = _Port()

    async def _method(**kwargs):
        return result

    setattr(port, method_name, _method)
    return port


def _assert_error_cases(use_case, kwargs: dict, method_name: str, cases: list[tuple[int, object, type[Exception]]]) -> None:
    for status, payload, exc_type in cases:
        port = _make_port(method_name, (status, payload))
        use_case.postgres_service = port
        with pytest.raises(exc_type):
            _run(use_case.execute(**kwargs))


def test_create_personal_course_lesson_success_and_errors() -> None:
    payload = {
        "lesson": {
            "id": 1,
            "course_id": 2,
            "title": "Intro",
            "content": "Body",
            "position": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
    }
    uc = CreatePersonalCourseLessonUseCase(postgres_service=_make_port("create_personal_course_lesson", (200, payload)))
    item = _run(uc.execute(token="jwt", course_id=2, title="Intro"))
    assert item.id == 1

    _assert_error_cases(
        uc,
        {"token": "jwt", "course_id": 2, "title": "Intro"},
        "create_personal_course_lesson",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (400, {"detail": "x"}, ValidationError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"lesson": "bad"}, DataIntegrityError),
        ],
    )


def test_get_personal_course_statistics_success_and_errors() -> None:
    payload = {
        "stats": {
            "course_id": 10,
            "course_title": "Course",
            "visitors": [
                {"user_id": 1, "user_name": "U1", "first_visit_at": "2026-01-01"},
                {"user_id": 2, "user_name": "skip", "first_visit_at": None},
                "bad",
            ],
            "lesson_completions": [
                {
                    "user_id": 1,
                    "user_name": "U1",
                    "lesson_id": 5,
                    "lesson_title": "L1",
                    "completed_at": "2026-01-02",
                },
                {"user_id": 2, "completed_at": None},
                "bad",
            ],
        }
    }
    uc = GetPersonalCourseStatisticsUseCase(
        postgres_service=_make_port("get_personal_course_statistics", (200, payload))
    )
    stats = _run(uc.execute(token="jwt", course_id=10))
    assert stats.course_id == 10
    assert len(stats.visitors) == 1
    assert len(stats.lesson_completions) == 1

    _assert_error_cases(
        uc,
        {"token": "jwt", "course_id": 10},
        "get_personal_course_statistics",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"stats": "bad"}, DataIntegrityError),
        ],
    )


def test_list_admin_author_role_requests_success_and_errors() -> None:
    payload = {
        "items": [
            {
                "id": 1,
                "user_id": 2,
                "user_email": "u@test.local",
                "user_nickname": "u",
                "message": "m",
                "status": "pending",
                "admin_message": None,
                "created_at": "2026-01-01",
                "updated_at": "2026-01-01",
            },
            {"id": "bad"},
        ]
    }
    uc = ListAdminAuthorRoleRequestsUseCase(
        postgres_service=_make_port("list_admin_author_role_requests", (200, payload))
    )
    items = _run(uc.execute(token="jwt", status=None, limit=10, offset=0))
    assert len(items) == 1
    assert items[0].id == 1

    _assert_error_cases(
        uc,
        {"token": "jwt", "status": None, "limit": 10, "offset": 0},
        "list_admin_author_role_requests",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )


def test_list_admin_course_lessons_success_and_errors() -> None:
    payload = {
        "items": [
            {
                "id": 1,
                "course_id": 2,
                "title": "L",
                "content": "C",
                "position": 1,
                "created_at": "2026",
                "updated_at": "2026",
            },
            {"id": "bad"},
        ]
    }
    uc = ListAdminCourseLessonsUseCase(postgres_service=_make_port("list_admin_course_lessons", (200, payload)))
    items = _run(uc.execute(token="jwt", course_id=2))
    assert len(items) == 1
    assert items[0].id == 1

    _assert_error_cases(
        uc,
        {"token": "jwt", "course_id": 2},
        "list_admin_course_lessons",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )


def test_list_admin_courses_tablatures_users_success_and_errors() -> None:
    uc_courses = ListAdminCoursesUseCase(
        postgres_service=_make_port(
            "list_admin_courses",
            (
                200,
                {
                    "items": [
                        {
                            "id": 1,
                            "title": "C",
                            "description": "D",
                            "author": "A",
                            "visibility": "public",
                            "tags": ["x", 1],
                            "cover_image_path": None,
                            "created_at": "2026",
                            "updated_at": "2026",
                        },
                        {"id": "bad"},
                    ]
                },
            ),
        )
    )
    courses = _run(uc_courses.execute(token="jwt", query=None, limit=10, offset=0))
    assert len(courses) == 1
    assert courses[0]["tags"] == ["x", "1"]

    _assert_error_cases(
        uc_courses,
        {"token": "jwt", "query": None, "limit": 10, "offset": 0},
        "list_admin_courses",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    uc_tabs = ListAdminTablaturesUseCase(
        postgres_service=_make_port(
            "list_admin_tablatures",
            (
                200,
                {
                    "items": [
                        {
                            "id": 1,
                            "task_id": 10,
                            "track_file_name": "song",
                            "author": "a",
                            "visibility": "public",
                            "result_path": None,
                            "created_at": "2026",
                            "updated_at": "2026",
                            "comments_count": 1,
                            "reactions_like_count": 2,
                            "reactions_fire_count": 3,
                            "reactions_wow_count": 4,
                        },
                        {"id": "bad"},
                    ]
                },
            ),
        )
    )
    tabs = _run(uc_tabs.execute(token="jwt", query=None, limit=10, offset=0))
    assert len(tabs) == 1
    assert tabs[0]["id"] == 1

    _assert_error_cases(
        uc_tabs,
        {"token": "jwt", "query": None, "limit": 10, "offset": 0},
        "list_admin_tablatures",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    uc_users = ListAdminUsersUseCase(
        postgres_service=_make_port(
            "list_admin_users",
            (200, {"items": [{"id": 1, "email": "u@test.local", "nickname": "u", "role": "user"}, {"id": "bad"}]}),
        )
    )
    users = _run(uc_users.execute(token="jwt", role=None, query=None, limit=10, offset=0))
    assert len(users) == 1
    assert users[0]["id"] == 1

    _assert_error_cases(
        uc_users,
        {"token": "jwt", "role": None, "query": None, "limit": 10, "offset": 0},
        "list_admin_users",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    port_bad_detail = _make_port("list_admin_users", (400, {"detail": "bad filter"}))
    uc_users.postgres_service = port_bad_detail
    with pytest.raises(ValidationError, match="bad filter"):
        _run(uc_users.execute(token="jwt", role=None, query=None, limit=10, offset=0))

    port_empty_detail = _make_port("list_admin_users", (400, {"detail": None}))
    uc_users.postgres_service = port_empty_detail
    with pytest.raises(ValidationError, match="Invalid users filter"):
        _run(uc_users.execute(token="jwt", role=None, query=None, limit=10, offset=0))


def test_list_admin_tablature_comments_success_and_errors() -> None:
    uc = ListAdminTablatureCommentsUseCase(
        postgres_service=_make_port("list_admin_tablature_comments", (200, {"items": [{"id": 1}]}))
    )
    assert _run(uc.execute(token="jwt", tablature_id=1, limit=10, offset=0))[0]["id"] == 1

    _assert_error_cases(
        uc,
        {"token": "jwt", "tablature_id": 1, "limit": 10, "offset": 0},
        "list_admin_tablature_comments",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )


def test_personal_lists_progress_and_visit_success_and_errors() -> None:
    uc_progress_list = ListPersonalCourseLessonProgressUseCase(
        postgres_service=_make_port(
            "list_personal_course_lesson_progress",
            (
                200,
                {"items": [{"lesson_id": 1, "is_completed": True, "completed_at": "2026", "updated_at": None}, "bad"]},
            ),
        )
    )
    progress_items = _run(uc_progress_list.execute(token="jwt", course_id=1))
    assert len(progress_items) == 1
    assert progress_items[0].lesson_id == 1

    _assert_error_cases(
        uc_progress_list,
        {"token": "jwt", "course_id": 1},
        "list_personal_course_lesson_progress",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    uc_lessons = ListPersonalCourseLessonsUseCase(
        postgres_service=_make_port(
            "list_personal_course_lessons",
            (
                200,
                {
                    "items": [
                        {"id": 1, "course_id": 1, "title": "L", "content": "C", "position": 1, "created_at": "2026", "updated_at": "2026"},
                        "bad",
                    ]
                },
            ),
        )
    )
    assert len(_run(uc_lessons.execute(token="jwt", course_id=1))) == 1

    _assert_error_cases(
        uc_lessons,
        {"token": "jwt", "course_id": 1},
        "list_personal_course_lessons",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    uc_courses = ListPersonalCoursesUseCase(
        postgres_service=_make_port(
            "list_personal_courses",
            (
                200,
                {
                    "items": [
                        {
                            "id": 1,
                            "title": "C",
                            "description": "D",
                            "author": "A",
                            "visibility": "private",
                            "tags": ["t", 1],
                            "cover_image_path": None,
                            "created_at": "2026",
                            "updated_at": "2026",
                        },
                        "bad",
                    ]
                },
            ),
        )
    )
    items = _run(uc_courses.execute(token="jwt", query=None, limit=10, offset=0))
    assert len(items) == 1
    assert items[0].tags == ["t", "1"]

    _assert_error_cases(
        uc_courses,
        {"token": "jwt", "query": None, "limit": 10, "offset": 0},
        "list_personal_courses",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"items": "bad"}, DataIntegrityError),
        ],
    )

    uc_set_progress = SetPersonalCourseLessonProgressUseCase(
        postgres_service=_make_port(
            "set_personal_course_lesson_progress",
            (200, {"progress": {"lesson_id": 1, "is_completed": True, "completed_at": "2026", "updated_at": "2026"}}),
        )
    )
    progress = _run(uc_set_progress.execute(token="jwt", course_id=1, lesson_id=1, completed=True))
    assert progress.lesson_id == 1

    _assert_error_cases(
        uc_set_progress,
        {"token": "jwt", "course_id": 1, "lesson_id": 1, "completed": True},
        "set_personal_course_lesson_progress",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"progress": "bad"}, DataIntegrityError),
        ],
    )

    uc_visit = TrackPersonalCourseVisitUseCase(
        postgres_service=_make_port(
            "track_personal_course_visit",
            (200, {"visit": {"user_id": 1, "course_id": 1, "is_first_visit": True, "first_visit_at": "2026"}}),
        )
    )
    visit = _run(uc_visit.execute(token="jwt", course_id=1))
    assert visit.user_id == 1

    _assert_error_cases(
        uc_visit,
        {"token": "jwt", "course_id": 1},
        "track_personal_course_visit",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"visit": "bad"}, DataIntegrityError),
        ],
    )


def test_update_admin_and_personal_use_cases_success_and_errors() -> None:
    uc_admin_req = UpdateAdminAuthorRoleRequestUseCase(
        postgres_service=_make_port(
            "update_admin_author_role_request",
            (
                200,
                {
                    "request": {
                        "id": 1,
                        "user_id": 2,
                        "user_email": "u@test.local",
                        "user_nickname": "u",
                        "message": "m",
                        "status": "approved",
                        "admin_message": "ok",
                        "created_at": "2026",
                        "updated_at": "2026",
                    }
                },
            ),
        )
    )
    req = _run(uc_admin_req.execute(token="jwt", request_id=1, status="approved", admin_message="ok"))
    assert req.status == "approved"

    _assert_error_cases(
        uc_admin_req,
        {"token": "jwt", "request_id": 1, "status": "approved", "admin_message": "ok"},
        "update_admin_author_role_request",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"request": "bad"}, DataIntegrityError),
        ],
    )

    for bad_payload, msg in [({"detail": "bad"}, "bad"), ({"detail": None}, "Invalid status or admin message")]:
        uc_admin_req.postgres_service = _make_port("update_admin_author_role_request", (400, bad_payload))
        with pytest.raises(ValidationError, match=msg):
            _run(uc_admin_req.execute(token="jwt", request_id=1, status="approved", admin_message="ok"))

    uc_course_vis = UpdateAdminCourseVisibilityUseCase(
        postgres_service=_make_port("update_admin_course_visibility", (200, {"course": {"id": 1}}))
    )
    assert _run(uc_course_vis.execute(token="jwt", course_id=1, visibility="public"))["id"] == 1

    _assert_error_cases(
        uc_course_vis,
        {"token": "jwt", "course_id": 1, "visibility": "public"},
        "update_admin_course_visibility",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"course": "bad"}, DataIntegrityError),
        ],
    )
    uc_course_vis.postgres_service = _make_port("update_admin_course_visibility", (400, {"detail": None}))
    with pytest.raises(ValidationError, match="Invalid visibility"):
        _run(uc_course_vis.execute(token="jwt", course_id=1, visibility="public"))

    uc_tab_vis = UpdateAdminTablatureVisibilityUseCase(
        postgres_service=_make_port("update_admin_tablature_visibility", (200, {"tablature": {"id": 1}}))
    )
    assert _run(uc_tab_vis.execute(token="jwt", tablature_id=1, visibility="public"))["id"] == 1
    _assert_error_cases(
        uc_tab_vis,
        {"token": "jwt", "tablature_id": 1, "visibility": "public"},
        "update_admin_tablature_visibility",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"tablature": "bad"}, DataIntegrityError),
        ],
    )
    uc_tab_vis.postgres_service = _make_port("update_admin_tablature_visibility", (400, {"detail": None}))
    with pytest.raises(ValidationError, match="Invalid visibility"):
        _run(uc_tab_vis.execute(token="jwt", tablature_id=1, visibility="public"))

    uc_user = UpdateAdminUserAccountUseCase(
        postgres_service=_make_port("update_admin_user_account", (200, {"user": {"id": 1, "email": "u@test.local"}}))
    )
    assert _run(uc_user.execute(token="jwt", user_id=1))["id"] == 1
    _assert_error_cases(
        uc_user,
        {"token": "jwt", "user_id": 1},
        "update_admin_user_account",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (403, {"detail": "x"}, ForbiddenError),
            (404, {"detail": "x"}, NotFoundError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"user": "bad"}, DataIntegrityError),
        ],
    )
    uc_user.postgres_service = _make_port("update_admin_user_account", (400, {"detail": None}))
    with pytest.raises(ValidationError, match="Invalid user update payload"):
        _run(uc_user.execute(token="jwt", user_id=1))

    uc_personal_course = UpdatePersonalCourseUseCase(
        postgres_service=_make_port(
            "update_personal_course",
            (
                200,
                {
                    "course": {
                        "id": 1,
                        "title": "C",
                        "description": "D",
                        "author": "A",
                        "visibility": "private",
                        "tags": ["x", 1],
                        "cover_image_path": None,
                        "created_at": "2026",
                        "updated_at": "2026",
                    }
                },
            ),
        )
    )
    course = _run(uc_personal_course.execute(token="jwt", course_id=1))
    assert course.tags == ["x", "1"]
    _assert_error_cases(
        uc_personal_course,
        {"token": "jwt", "course_id": 1},
        "update_personal_course",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (400, {"detail": "x"}, ValidationError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"course": "bad"}, DataIntegrityError),
        ],
    )

    uc_personal_lesson = UpdatePersonalCourseLessonUseCase(
        postgres_service=_make_port(
            "update_personal_course_lesson",
            (
                200,
                {
                    "lesson": {
                        "id": 1,
                        "course_id": 1,
                        "title": "L",
                        "content": "C",
                        "position": 1,
                        "created_at": "2026",
                        "updated_at": "2026",
                    }
                },
            ),
        )
    )
    lesson = _run(uc_personal_lesson.execute(token="jwt", course_id=1, lesson_id=1))
    assert lesson.id == 1
    _assert_error_cases(
        uc_personal_lesson,
        {"token": "jwt", "course_id": 1, "lesson_id": 1},
        "update_personal_course_lesson",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (400, {"detail": "x"}, ValidationError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"lesson": "bad"}, DataIntegrityError),
        ],
    )

    uc_personal_tab = UpdatePersonalTablatureUseCase(
        postgres_service=_make_port("update_personal_tablature", (200, {"tablature": {"id": 1}}))
    )
    assert _run(uc_personal_tab.execute(token="jwt", tablature_id=1))["id"] == 1
    _assert_error_cases(
        uc_personal_tab,
        {"token": "jwt", "tablature_id": 1},
        "update_personal_tablature",
        [
            (401, {"detail": "x"}, AuthenticationError),
            (404, {"detail": "x"}, NotFoundError),
            (409, {"detail": "x"}, ConflictError),
            (400, {"detail": "x"}, ValidationError),
            (500, {"detail": "x"}, ExternalServiceError),
            (200, "not-json", DataIntegrityError),
            (200, {"tablature": "bad"}, DataIntegrityError),
        ],
    )

