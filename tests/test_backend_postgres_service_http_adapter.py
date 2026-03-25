from __future__ import annotations

import asyncio
import inspect
from typing import Any

import httpx
import pytest

from backend_app.adapters.postgres_service_http import PostgresServiceHttpAdapter
from backend_app.domain.errors import ExternalServiceError


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        json_exc: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self._json_exc = json_exc

    def json(self) -> Any:
        if self._json_exc is not None:
            raise self._json_exc
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, *, response: _FakeResponse | None = None, error: Exception | None = None, **kwargs) -> None:
        self.response = response or _FakeResponse(status_code=200, json_data={"ok": True})
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response

    async def post(self, url: str, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response

    async def patch(self, url: str, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response

    async def delete(self, url: str, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response


def _build_kwargs(method_name: str, sig: inspect.Signature) -> dict[str, Any]:
    values: dict[str, Any] = {
        "token": "jwt-token",
        "query": "q",
        "q": "q",
        "limit": 50,
        "offset": 0,
        "course_id": 1,
        "lesson_id": 1,
        "tablature_id": 1,
        "comment_id": 1,
        "user_id": 1,
        "request_id": 1,
        "email": "user@test.local",
        "password": "secret123",
        "nickname": "nick",
        "message": "please approve",
        "status": "approved",
        "admin_message": "ok",
        "visibility": "public",
        "reaction_type": "like",
        "title": "Title",
        "description": "Description",
        "content": "Content",
        "position": 1,
        "completed": True,
        "tags": ["rock"],
        "cover_image_path": "/api/media/covers/1.png",
        "track_file_name": "track.mp3",
        "json_format": {"lines": []},
    }

    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if name in values:
            kwargs[name] = values[name]
            continue
        if param.default is not inspect._empty:
            # Pass non-empty values for optional params to execute payload-building branches.
            if param.default is None:
                kwargs[name] = "x"
            else:
                kwargs[name] = param.default
            continue
        kwargs[name] = "x"
    return kwargs


def test_postgres_http_adapter_all_async_methods_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend_app.adapters.postgres_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(response=_FakeResponse(status_code=200, json_data={"ok": True})),
    )
    adapter = PostgresServiceHttpAdapter(base_url="http://postgres.local/", timeout_sec=5.0)

    methods = [
        (name, fn)
        for name, fn in inspect.getmembers(PostgresServiceHttpAdapter, predicate=inspect.iscoroutinefunction)
        if not name.startswith("_")
    ]
    assert methods, "Expected async methods in PostgresServiceHttpAdapter"

    for name, fn in methods:
        sig = inspect.signature(fn)
        kwargs = _build_kwargs(name, sig)
        status, payload = asyncio.run(fn(adapter, **kwargs))
        assert status == 200, f"{name} should return status code"
        assert isinstance(payload, dict), f"{name} should return parsed JSON payload"


def test_postgres_http_adapter_falls_back_to_text_when_json_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend_app.adapters.postgres_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            response=_FakeResponse(status_code=418, text="teapot", json_exc=ValueError("bad json"))
        ),
    )
    adapter = PostgresServiceHttpAdapter(base_url="http://postgres.local", timeout_sec=5.0)

    status, payload = asyncio.run(adapter.list_public_tablatures(query="x", limit=10, offset=0))
    assert status == 418
    assert payload == "teapot"


def test_postgres_http_adapter_wraps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend_app.adapters.postgres_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("network boom")),
    )
    adapter = PostgresServiceHttpAdapter(base_url="http://postgres.local", timeout_sec=5.0)

    with pytest.raises(ExternalServiceError, match="request failed"):
        asyncio.run(adapter.list_public_tablatures(query=None, limit=10, offset=0))

