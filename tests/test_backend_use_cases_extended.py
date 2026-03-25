from __future__ import annotations

import asyncio
import json

import pytest

from backend_app.application.use_cases.create_course import CreateCourseUseCase
from backend_app.application.use_cases.download_public_tablature_json import DownloadPublicTablatureJsonUseCase
from backend_app.application.use_cases.get_current_user import GetCurrentUserUseCase
from backend_app.application.use_cases.get_job_by_id import GetJobByIdUseCase
from backend_app.application.use_cases.get_pdf_by_job_id import GetPdfByJobIdUseCase
from backend_app.application.use_cases.get_public_tablature_by_id import GetPublicTablatureByIdUseCase
from backend_app.application.use_cases.get_public_tablature_reactions import GetPublicTablatureReactionsUseCase
from backend_app.application.use_cases.get_tablature_by_job_id import GetTablatureByJobIdUseCase
from backend_app.application.use_cases.list_public_course_lessons import ListPublicCourseLessonsUseCase
from backend_app.application.use_cases.list_public_courses import ListPublicCoursesUseCase
from backend_app.application.use_cases.list_public_tablature_comments import ListPublicTablatureCommentsUseCase
from backend_app.application.use_cases.list_public_tablatures import ListPublicTablaturesUseCase
from backend_app.application.use_cases.login_user import LoginUserUseCase
from backend_app.application.use_cases.register_user import RegisterUserUseCase
from backend_app.application.use_cases.set_public_tablature_reaction import SetPublicTablatureReactionUseCase
from backend_app.application.use_cases.update_current_user import UpdateCurrentUserUseCase
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
    port.calls = []

    async def _method(**kwargs):
        port.calls.append(kwargs)
        return result

    setattr(port, method_name, _method)
    return port


def test_register_user_success() -> None:
    user = {"id": 1, "email": "u@test.local"}
    port = _make_port("register_user", (200, {"user": user}))
    use_case = RegisterUserUseCase(postgres_service=port)

    result = _run(use_case.execute(email="u@test.local", password="secret12", nickname="nick"))
    assert result == user
    assert port.calls[0]["email"] == "u@test.local"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (409, ConflictError),
        (400, ValidationError),
    ],
)
def test_register_user_status_mapping(status: int, error_type: type[Exception]) -> None:
    port = _make_port("register_user", (status, {"detail": "bad"}))
    use_case = RegisterUserUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(email="a@b.c", password="secret12", nickname="n"))


def test_register_user_non_200_raises_external_error() -> None:
    port = _make_port("register_user", (503, "service unavailable"))
    use_case = RegisterUserUseCase(postgres_service=port)
    with pytest.raises(ExternalServiceError, match="PostgreSQL service error"):
        _run(use_case.execute(email="a@b.c", password="secret12", nickname="n"))


@pytest.mark.parametrize("payload", ["not-dict", {"foo": "bar"}])
def test_register_user_payload_validation(payload: object) -> None:
    port = _make_port("register_user", (200, payload))
    use_case = RegisterUserUseCase(postgres_service=port)
    with pytest.raises(DataIntegrityError):
        _run(use_case.execute(email="a@b.c", password="secret12", nickname="n"))


def test_login_user_success() -> None:
    payload = {"access_token": "jwt", "token_type": "bearer"}
    port = _make_port("login_user", (200, payload))
    use_case = LoginUserUseCase(postgres_service=port)
    result = _run(use_case.execute(email="u@test.local", password="secret12"))
    assert result["access_token"] == "jwt"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, AuthenticationError),
        (400, ValidationError),
    ],
)
def test_login_user_status_mapping(status: int, error_type: type[Exception]) -> None:
    port = _make_port("login_user", (status, {"detail": "bad"}))
    use_case = LoginUserUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(email="u@test.local", password="secret12"))


def test_login_user_non_200_raises_external_error() -> None:
    port = _make_port("login_user", (500, {"detail": "err"}))
    use_case = LoginUserUseCase(postgres_service=port)
    with pytest.raises(ExternalServiceError):
        _run(use_case.execute(email="u@test.local", password="secret12"))


@pytest.mark.parametrize("payload", ["str-payload", {"foo": "bar"}])
def test_login_user_payload_validation(payload: object) -> None:
    port = _make_port("login_user", (200, payload))
    use_case = LoginUserUseCase(postgres_service=port)
    with pytest.raises(DataIntegrityError):
        _run(use_case.execute(email="u@test.local", password="secret12"))


def test_get_current_user_success() -> None:
    user = {"id": 9, "email": "u@test.local"}
    port = _make_port("get_current_user", (200, {"user": user}))
    use_case = GetCurrentUserUseCase(postgres_service=port)
    result = _run(use_case.execute(token="jwt"))
    assert result == user


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad token"}, AuthenticationError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_get_current_user_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_current_user", (status, payload))
    use_case = GetCurrentUserUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt"))


def test_update_current_user_success() -> None:
    user = {"id": 9, "nickname": "newnick"}
    port = _make_port("update_current_user", (200, {"user": user}))
    use_case = UpdateCurrentUserUseCase(postgres_service=port)
    result = _run(use_case.execute(token="jwt", nickname="newnick"))
    assert result["nickname"] == "newnick"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad token"}, AuthenticationError),
        (400, {"detail": "invalid"}, ValidationError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_update_current_user_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("update_current_user", (status, payload))
    use_case = UpdateCurrentUserUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt", nickname="nick"))


def test_get_job_by_id_success() -> None:
    payload = {"job": {"id": "6", "status": "queued"}}
    port = _make_port("get_job", (200, payload))
    use_case = GetJobByIdUseCase(ml_service=port)
    result = _run(use_case.execute(job_id="6"))
    assert result.id == "6"
    assert result.status == "queued"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "not found"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
        (200, {"job": {"id": "6"}}, DataIntegrityError),
    ],
)
def test_get_job_by_id_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_job", (status, payload))
    use_case = GetJobByIdUseCase(ml_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(job_id="6"))


def test_get_tablature_by_job_id_success() -> None:
    payload = {"tablature": {"meta": {}, "lines": []}}
    port = _make_port("get_tablature", (200, payload))
    use_case = GetTablatureByJobIdUseCase(ml_service=port)
    result = _run(use_case.execute(job_id="6"))
    assert result.job_id == "6"
    assert isinstance(result.tablature, dict)


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "not found"}, NotFoundError),
        (409, {"detail": "not ready"}, ConflictError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_get_tablature_by_job_id_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_tablature", (status, payload))
    use_case = GetTablatureByJobIdUseCase(ml_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(job_id="6"))


def test_get_pdf_by_job_id_success() -> None:
    port = _make_port("get_pdf", (200, b"%PDF"))
    use_case = GetPdfByJobIdUseCase(ml_service=port)
    result = _run(use_case.execute(job_id="6"))
    assert result.content.startswith(b"%PDF")
    assert result.download_filename == "6.pdf"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "not found"}, NotFoundError),
        (409, {"detail": "not ready"}, ConflictError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, {"not": "binary"}, DataIntegrityError),
    ],
)
def test_get_pdf_by_job_id_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_pdf", (status, payload))
    use_case = GetPdfByJobIdUseCase(ml_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(job_id="6"))


def test_get_public_tablature_by_id_success() -> None:
    payload = {"tablature": {"id": 3, "json_format": {"lines": []}}}
    port = _make_port("get_public_tablature", (200, payload))
    use_case = GetPublicTablatureByIdUseCase(postgres_service=port)
    result = _run(use_case.execute(tablature_id=3))
    assert result["id"] == 3


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "not found"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_get_public_tablature_by_id_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_public_tablature", (status, payload))
    use_case = GetPublicTablatureByIdUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(tablature_id=3))


def test_list_public_tablatures_parses_and_skips_invalid_rows() -> None:
    payload = {
        "items": [
            {
                "id": 1,
                "task_id": 4,
                "track_file_name": "song",
                "author": "nick",
                "result_path": "/tmp/a.json",
                "created_at": "2026-01-01",
            },
            "bad-row",
            {"id": "oops"},
        ]
    }
    port = _make_port("list_public_tablatures", (200, payload))
    use_case = ListPublicTablaturesUseCase(postgres_service=port)
    result = _run(use_case.execute(query=None, limit=10, offset=0))
    assert len(result) == 1
    assert result[0].id == 1


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"items": "not-list"}, DataIntegrityError),
    ],
)
def test_list_public_tablatures_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("list_public_tablatures", (status, payload))
    use_case = ListPublicTablaturesUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(query=None, limit=10, offset=0))


def test_list_public_courses_parses_and_skips_invalid_rows() -> None:
    payload = {
        "items": [
            {
                "id": 5,
                "title": "Course",
                "description": "Desc",
                "author": "nick",
                "visibility": "public",
                "tags": ["rock", 1],
                "cover_image_path": "/api/media/covers/1.png",
                "created_at": "2026-01-01",
                "updated_at": "2026-01-02",
            },
            {"id": None},
        ]
    }
    port = _make_port("list_public_courses", (200, payload))
    use_case = ListPublicCoursesUseCase(postgres_service=port)
    result = _run(use_case.execute(query=None, limit=10, offset=0))
    assert len(result) == 1
    assert result[0].id == 5
    assert result[0].tags == ["rock", "1"]


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"items": {}}, DataIntegrityError),
    ],
)
def test_list_public_courses_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("list_public_courses", (status, payload))
    use_case = ListPublicCoursesUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(query=None, limit=10, offset=0))


def test_list_public_course_lessons_parses_rows() -> None:
    payload = {
        "items": [
            {
                "id": 11,
                "course_id": 5,
                "title": "Intro",
                "content": "text",
                "position": 1,
                "created_at": "2026-01-01",
                "updated_at": "2026-01-02",
            }
        ]
    }
    port = _make_port("list_public_course_lessons", (200, payload))
    use_case = ListPublicCourseLessonsUseCase(postgres_service=port)
    result = _run(use_case.execute(course_id=5))
    assert len(result) == 1
    assert result[0].course_id == 5


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "missing"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"items": {}}, DataIntegrityError),
    ],
)
def test_list_public_course_lessons_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("list_public_course_lessons", (status, payload))
    use_case = ListPublicCourseLessonsUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(course_id=5))


def test_list_public_tablature_comments_success() -> None:
    payload = {"items": [{"id": 1, "content": "ok"}]}
    port = _make_port("list_public_tablature_comments", (200, payload))
    use_case = ListPublicTablatureCommentsUseCase(postgres_service=port)
    result = _run(use_case.execute(tablature_id=3, limit=10, offset=0))
    assert result[0]["content"] == "ok"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "missing"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"items": {}}, DataIntegrityError),
    ],
)
def test_list_public_tablature_comments_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("list_public_tablature_comments", (status, payload))
    use_case = ListPublicTablatureCommentsUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(tablature_id=3, limit=10, offset=0))


def test_get_public_tablature_reactions_success() -> None:
    payload = {"reactions": {"like": 2, "fire": 1, "wow": 0}}
    port = _make_port("get_public_tablature_reactions", (200, payload))
    use_case = GetPublicTablatureReactionsUseCase(postgres_service=port)
    result = _run(use_case.execute(tablature_id=5, token=None))
    assert result["like"] == 2


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (404, {"detail": "missing"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_get_public_tablature_reactions_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_public_tablature_reactions", (status, payload))
    use_case = GetPublicTablatureReactionsUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(tablature_id=5, token="jwt"))


def test_set_public_tablature_reaction_success() -> None:
    payload = {"reactions": {"like": 3, "fire": 0, "wow": 1}}
    port = _make_port("set_public_tablature_reaction", (200, payload))
    use_case = SetPublicTablatureReactionUseCase(postgres_service=port)
    result = _run(use_case.execute(token="jwt", tablature_id=5, reaction_type="like"))
    assert result["like"] == 3


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (401, {"detail": "bad"}, AuthenticationError),
        (404, {"detail": "missing"}, NotFoundError),
        (400, {"detail": "invalid"}, ValidationError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_set_public_tablature_reaction_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("set_public_tablature_reaction", (status, payload))
    use_case = SetPublicTablatureReactionUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt", tablature_id=5, reaction_type="like"))


def test_download_public_tablature_json_success() -> None:
    json_format = {"meta": {"tempo": 120}, "lines": []}
    payload = {"tablature": {"id": 10, "json_format": json_format}}
    port = _make_port("get_public_tablature", (200, payload))
    use_case = DownloadPublicTablatureJsonUseCase(postgres_service=port)

    artifact = _run(use_case.execute(tablature_id=10))
    assert artifact.download_filename == "community-tablature-10.json"
    assert json.loads(artifact.content.decode("utf-8")) == json_format


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (404, {"detail": "missing"}, NotFoundError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"tablature": {}}, DataIntegrityError),
    ],
)
def test_download_public_tablature_json_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("get_public_tablature", (status, payload))
    use_case = DownloadPublicTablatureJsonUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(tablature_id=10))


def test_create_course_success() -> None:
    payload = {
        "course": {
            "id": 7,
            "title": "Course",
            "description": "Desc",
            "author": "nick",
            "visibility": "public",
            "tags": ["rock"],
            "cover_image_path": "/api/media/covers/7.png",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-02",
        }
    }
    port = _make_port("create_course", (200, payload))
    use_case = CreateCourseUseCase(postgres_service=port)
    item = _run(
        use_case.execute(
            token="jwt",
            title="Course",
            description="Desc",
            visibility="public",
            tags=["rock"],
            cover_image_path="/api/media/covers/7.png",
        )
    )
    assert item.id == 7
    assert item.author == "nick"


@pytest.mark.parametrize(
    ("status", "payload", "error_type"),
    [
        (400, {"detail": "bad"}, ValidationError),
        (401, {"detail": "bad"}, AuthenticationError),
        (403, {"detail": "bad"}, ForbiddenError),
        (500, {"detail": "boom"}, ExternalServiceError),
        (200, "not-json", DataIntegrityError),
        (200, {"foo": "bar"}, DataIntegrityError),
    ],
)
def test_create_course_error_mapping(status: int, payload: object, error_type: type[Exception]) -> None:
    port = _make_port("create_course", (status, payload))
    use_case = CreateCourseUseCase(postgres_service=port)
    with pytest.raises(error_type):
        _run(use_case.execute(token="jwt", title="Course"))
