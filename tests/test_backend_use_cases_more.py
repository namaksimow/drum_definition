from __future__ import annotations

import asyncio

import pytest

from backend_app.application.use_cases.create_personal_author_role_request import (
    CreatePersonalAuthorRoleRequestUseCase,
)
from backend_app.application.use_cases.create_public_tablature_comment import (
    CreatePublicTablatureCommentUseCase,
)
from backend_app.application.use_cases.delete_admin_course import DeleteAdminCourseUseCase
from backend_app.application.use_cases.delete_admin_tablature import DeleteAdminTablatureUseCase
from backend_app.application.use_cases.delete_admin_tablature_comment import (
    DeleteAdminTablatureCommentUseCase,
)
from backend_app.application.use_cases.delete_admin_user import DeleteAdminUserUseCase
from backend_app.application.use_cases.delete_personal_course import DeletePersonalCourseUseCase
from backend_app.application.use_cases.delete_personal_course_lesson import (
    DeletePersonalCourseLessonUseCase,
)
from backend_app.application.use_cases.get_admin_course_by_id import GetAdminCourseByIdUseCase
from backend_app.application.use_cases.get_admin_tablature_by_id import GetAdminTablatureByIdUseCase
from backend_app.application.use_cases.get_personal_author_role_request import (
    GetPersonalAuthorRoleRequestUseCase,
)
from backend_app.application.use_cases.get_personal_tablature_by_id import (
    GetPersonalTablatureByIdUseCase,
)
from backend_app.application.use_cases.list_personal_tablatures import ListPersonalTablaturesUseCase
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


def test_create_personal_author_role_request_success() -> None:
    payload = {
        "request": {
            "id": 1,
            "user_id": 5,
            "message": "please",
            "status": "pending",
            "admin_message": None,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
    }
    port = _make_port("create_personal_author_role_request", (200, payload))
    use_case = CreatePersonalAuthorRoleRequestUseCase(postgres_service=port)
    item = _run(use_case.execute(token="jwt", message="please"))
    assert item.id == 1
    assert item.user_id == 5


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (409, {"detail": "dup"}, ConflictError),
        (400, {"detail": "bad"}, ValidationError),
        (500, {"detail": "err"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"request": "bad"}, DataIntegrityError),
    ],
)
def test_create_personal_author_role_request_errors(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("create_personal_author_role_request", (status, payload))
    use_case = CreatePersonalAuthorRoleRequestUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt", message="please"))


def test_create_public_tablature_comment_success() -> None:
    port = _make_port("create_public_tablature_comment", (200, {"comment": {"id": 1, "content": "ok"}}))
    use_case = CreatePublicTablatureCommentUseCase(postgres_service=port)
    comment = _run(use_case.execute(token="jwt", tablature_id=1, content="ok"))
    assert comment["id"] == 1


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (404, {"detail": "missing"}, NotFoundError),
        (400, {"detail": "bad"}, ValidationError),
        (500, {"detail": "err"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"comment": "bad"}, DataIntegrityError),
    ],
)
def test_create_public_tablature_comment_errors(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("create_public_tablature_comment", (status, payload))
    use_case = CreatePublicTablatureCommentUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt", tablature_id=1, content="ok"))


@pytest.mark.parametrize(
    ("use_case_cls", "method_name", "kwargs"),
    [
        (DeleteAdminCourseUseCase, "delete_admin_course", {"token": "jwt", "course_id": 1}),
        (DeleteAdminTablatureUseCase, "delete_admin_tablature", {"token": "jwt", "tablature_id": 1}),
        (
            DeleteAdminTablatureCommentUseCase,
            "delete_admin_tablature_comment",
            {"token": "jwt", "tablature_id": 1, "comment_id": 1},
        ),
        (DeleteAdminUserUseCase, "delete_admin_user", {"token": "jwt", "user_id": 1}),
        (DeletePersonalCourseUseCase, "delete_personal_course", {"token": "jwt", "course_id": 1}),
        (
            DeletePersonalCourseLessonUseCase,
            "delete_personal_course_lesson",
            {"token": "jwt", "course_id": 1, "lesson_id": 1},
        ),
    ],
)
def test_delete_use_cases_success(use_case_cls, method_name: str, kwargs: dict) -> None:
    port = _make_port(method_name, (200, {"deleted": True}))
    use_case = use_case_cls(postgres_service=port)
    assert _run(use_case.execute(**kwargs)) is True


@pytest.mark.parametrize(
    ("use_case_cls", "method_name", "kwargs", "status", "error_type"),
    [
        (DeleteAdminCourseUseCase, "delete_admin_course", {"token": "jwt", "course_id": 1}, 403, ForbiddenError),
        (
            DeleteAdminTablatureUseCase,
            "delete_admin_tablature",
            {"token": "jwt", "tablature_id": 1},
            404,
            NotFoundError,
        ),
        (
            DeleteAdminTablatureCommentUseCase,
            "delete_admin_tablature_comment",
            {"token": "jwt", "tablature_id": 1, "comment_id": 1},
            401,
            AuthenticationError,
        ),
        (DeleteAdminUserUseCase, "delete_admin_user", {"token": "jwt", "user_id": 1}, 404, NotFoundError),
        (DeletePersonalCourseUseCase, "delete_personal_course", {"token": "jwt", "course_id": 1}, 401, AuthenticationError),
        (
            DeletePersonalCourseLessonUseCase,
            "delete_personal_course_lesson",
            {"token": "jwt", "course_id": 1, "lesson_id": 1},
            404,
            NotFoundError,
        ),
    ],
)
def test_delete_use_cases_error_mapping(
    use_case_cls, method_name: str, kwargs: dict, status: int, error_type: type[Exception]
) -> None:
    port = _make_port(method_name, (status, {"detail": "x"}))
    use_case = use_case_cls(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(**kwargs))


def test_get_admin_course_and_tablature_success() -> None:
    course_port = _make_port("get_admin_course", (200, {"course": {"id": 10}}))
    tab_port = _make_port("get_admin_tablature", (200, {"tablature": {"id": 20}}))

    course_uc = GetAdminCourseByIdUseCase(postgres_service=course_port)
    tab_uc = GetAdminTablatureByIdUseCase(postgres_service=tab_port)

    assert _run(course_uc.execute(token="jwt", course_id=10))["id"] == 10
    assert _run(tab_uc.execute(token="jwt", tablature_id=20))["id"] == 20


@pytest.mark.parametrize(
    ("use_case_cls", "method_name", "kwargs", "status", "payload", "error_type"),
    [
        (GetAdminCourseByIdUseCase, "get_admin_course", {"token": "jwt", "course_id": 1}, 403, {"detail": "x"}, ForbiddenError),
        (GetAdminCourseByIdUseCase, "get_admin_course", {"token": "jwt", "course_id": 1}, 200, {"course": "bad"}, DataIntegrityError),
        (
            GetAdminTablatureByIdUseCase,
            "get_admin_tablature",
            {"token": "jwt", "tablature_id": 1},
            404,
            {"detail": "x"},
            NotFoundError,
        ),
        (
            GetAdminTablatureByIdUseCase,
            "get_admin_tablature",
            {"token": "jwt", "tablature_id": 1},
            500,
            {"detail": "x"},
            ExternalServiceError,
        ),
    ],
)
def test_get_admin_use_cases_error_mapping(
    use_case_cls, method_name: str, kwargs: dict, status: int, payload: object, error_type: type[Exception]
) -> None:
    port = _make_port(method_name, (status, payload))
    use_case = use_case_cls(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(**kwargs))


def test_get_personal_author_role_request_success_and_none() -> None:
    payload_none = {"request": None}
    payload_value = {
        "request": {
            "id": 1,
            "user_id": 5,
            "message": "hello",
            "status": "rejected",
            "admin_message": "reason",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-02",
        }
    }
    port_none = _make_port("get_personal_author_role_request", (200, payload_none))
    port_val = _make_port("get_personal_author_role_request", (200, payload_value))
    uc_none = GetPersonalAuthorRoleRequestUseCase(postgres_service=port_none)
    uc_val = GetPersonalAuthorRoleRequestUseCase(postgres_service=port_val)

    assert _run(uc_none.execute(token="jwt")) is None
    assert _run(uc_val.execute(token="jwt")).admin_message == "reason"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (500, {"detail": "err"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"request": "bad"}, DataIntegrityError),
    ],
)
def test_get_personal_author_role_request_errors(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_personal_author_role_request", (status, payload))
    uc = GetPersonalAuthorRoleRequestUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(uc.execute(token="jwt"))


def test_get_personal_tablature_success() -> None:
    port = _make_port("get_personal_tablature", (200, {"tablature": {"id": 3}}))
    uc = GetPersonalTablatureByIdUseCase(postgres_service=port)
    assert _run(uc.execute(token="jwt", tablature_id=3))["id"] == 3


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (404, {"detail": "missing"}, NotFoundError),
        (500, {"detail": "err"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"tablature": "bad"}, DataIntegrityError),
    ],
)
def test_get_personal_tablature_errors(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_personal_tablature", (status, payload))
    uc = GetPersonalTablatureByIdUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(uc.execute(token="jwt", tablature_id=3))


def test_list_personal_tablatures_success_and_skips_invalid_rows() -> None:
    payload = {
        "items": [
            {"id": 1, "task_id": 2, "track_file_name": "song", "author": "nick", "result_path": None, "created_at": "2026"},
            {"id": "bad"},
        ]
    }
    port = _make_port("list_personal_tablatures", (200, payload))
    uc = ListPersonalTablaturesUseCase(postgres_service=port)
    items = _run(uc.execute(token="jwt", query=None, limit=10, offset=0))
    assert len(items) == 1
    assert items[0].id == 1


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (500, {"detail": "err"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"items": "bad"}, DataIntegrityError),
    ],
)
def test_list_personal_tablatures_errors(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("list_personal_tablatures", (status, payload))
    uc = ListPersonalTablaturesUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(uc.execute(token="jwt", query=None, limit=10, offset=0))

