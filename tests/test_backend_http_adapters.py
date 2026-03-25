from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from backend_app.adapters.ml_service_http import MlServiceHttpAdapter
from backend_app.adapters.object_storage_http import ObjectStorageHttpAdapter
from backend_app.domain.errors import ExternalServiceError


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
        content: bytes = b"",
        headers: dict[str, str] | None = None,
        json_exc: Exception | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = content
        self.headers = headers or {}
        self._json_exc = json_exc

    def json(self) -> Any:
        if self._json_exc is not None:
            raise self._json_exc
        return self._json_data


class _FakeAsyncClient:
    def __init__(self, *, post=None, get=None, put=None, error: Exception | None = None, **kwargs) -> None:
        self._post = post
        self._get = get
        self._put = put
        self._error = error
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, **kwargs):
        self.calls.append(("post", url, kwargs))
        if self._error is not None:
            raise self._error
        if callable(self._post):
            return self._post(url, kwargs)
        return self._post

    async def get(self, url: str, **kwargs):
        self.calls.append(("get", url, kwargs))
        if self._error is not None:
            raise self._error
        if callable(self._get):
            return self._get(url, kwargs)
        return self._get

    async def put(self, url: str, **kwargs):
        self.calls.append(("put", url, kwargs))
        if self._error is not None:
            raise self._error
        if callable(self._put):
            return self._put(url, kwargs)
        return self._put


def _run(coro):
    return asyncio.run(coro)


def test_ml_service_http_submit_upload_success(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _FakeResponse(status_code=200, json_data={"job": {"id": "1", "status": "queued"}})

    def _factory(*args, **kwargs):
        return _FakeAsyncClient(post=response)

    monkeypatch.setattr("backend_app.adapters.ml_service_http.httpx.AsyncClient", _factory)
    adapter = MlServiceHttpAdapter(base_url="http://ml.local/", timeout_sec=5.0)
    payload = _run(
        adapter.submit_upload(
            filename="track.mp3",
            data=b"audio",
            content_type="audio/mpeg",
            user_id=5,
            tablature_name="Track Name",
        )
    )
    assert payload["job"]["id"] == "1"


def test_ml_service_http_submit_upload_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = MlServiceHttpAdapter(base_url="http://ml.local", timeout_sec=5.0)

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(ExternalServiceError, match="upload request failed"):
        _run(adapter.submit_upload(filename="track.mp3", data=b"a", content_type="audio/mpeg"))

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(post=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(ExternalServiceError, match="upload error"):
        _run(adapter.submit_upload(filename="track.mp3", data=b"a", content_type="audio/mpeg"))

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(post=_FakeResponse(status_code=200, json_data=["bad"])),
    )
    with pytest.raises(ExternalServiceError, match="invalid upload payload"):
        _run(adapter.submit_upload(filename="track.mp3", data=b"a", content_type="audio/mpeg"))


def test_ml_service_http_getters_parse_json_or_text(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = MlServiceHttpAdapter(base_url="http://ml.local", timeout_sec=5.0)

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, json_data={"job": {"id": "6"}})),
    )
    status, payload = _run(adapter.get_job(job_id="6"))
    assert status == 200
    assert isinstance(payload, dict)

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            get=_FakeResponse(status_code=404, text="missing", json_exc=ValueError("bad-json"))
        ),
    )
    status, payload = _run(adapter.get_tablature(job_id="6"))
    assert status == 404
    assert payload == "missing"

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, content=b"%PDF")),
    )
    status, payload = _run(adapter.get_pdf(job_id="6"))
    assert status == 200
    assert payload == b"%PDF"

    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            get=_FakeResponse(status_code=409, text="not-ready", json_exc=ValueError("bad-json"))
        ),
    )
    status, payload = _run(adapter.get_pdf(job_id="6"))
    assert status == 409
    assert payload == "not-ready"


def test_ml_service_http_getters_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = MlServiceHttpAdapter(base_url="http://ml.local", timeout_sec=5.0)
    monkeypatch.setattr(
        "backend_app.adapters.ml_service_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(ExternalServiceError, match="get-job request failed"):
        _run(adapter.get_job(job_id="6"))
    with pytest.raises(ExternalServiceError, match="get-tablature request failed"):
        _run(adapter.get_tablature(job_id="6"))
    with pytest.raises(ExternalServiceError, match="get-pdf request failed"):
        _run(adapter.get_pdf(job_id="6"))


def test_object_storage_upload_validation_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ObjectStorageHttpAdapter(base_url="http://minio.local/", timeout_sec=5.0)
    with pytest.raises(ValueError, match="Object key is required"):
        _run(adapter.upload_bytes(object_key=" ", data=b"x"))
    with pytest.raises(ValueError, match="Data is empty"):
        _run(adapter.upload_bytes(object_key="k", data=b""))

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(put=_FakeResponse(status_code=200, json_data={"object_key": "k2"})),
    )
    key = _run(adapter.upload_bytes(object_key="/k1", data=b"x", content_type="text/plain"))
    assert key == "k2"

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(put=_FakeResponse(status_code=200, json_data={})),
    )
    key = _run(adapter.upload_bytes(object_key="/k1", data=b"x"))
    assert key == "k1"


def test_object_storage_upload_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ObjectStorageHttpAdapter(base_url="http://minio.local", timeout_sec=5.0)
    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(ExternalServiceError, match="upload failed"):
        _run(adapter.upload_bytes(object_key="k", data=b"x"))

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(put=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(ExternalServiceError, match="upload failed"):
        _run(adapter.upload_bytes(object_key="k", data=b"x"))


def test_object_storage_get_bytes_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ObjectStorageHttpAdapter(base_url="http://minio.local", timeout_sec=5.0)
    with pytest.raises(FileNotFoundError, match="Object key is empty"):
        _run(adapter.get_bytes(object_key=" "))

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(
            get=_FakeResponse(status_code=200, content=b"abc", headers={"Content-Type": "image/png"})
        ),
    )
    payload, media = _run(adapter.get_bytes(object_key="/img"))
    assert payload == b"abc"
    assert media == "image/png"

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, content=b"abc")),
    )
    _, media = _run(adapter.get_bytes(object_key="/img"))
    assert media == "application/octet-stream"

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=404, text="missing")),
    )
    with pytest.raises(FileNotFoundError, match="Object not found"):
        _run(adapter.get_bytes(object_key="img"))

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(ExternalServiceError, match="get failed"):
        _run(adapter.get_bytes(object_key="img"))

    monkeypatch.setattr(
        "backend_app.adapters.object_storage_http.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(ExternalServiceError, match="get failed"):
        _run(adapter.get_bytes(object_key="img"))

