from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest

from ml_service.adapters.minio.http_storage import MinioHttpFileStorage
from ml_service.adapters.queue.http_queue import QueueServiceHttpAdapter


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        text: str = "",
        json_data: Any = None,
        content: bytes = b"",
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._json_data = json_data
        self.content = content

    def json(self) -> Any:
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


def test_queue_http_publish_success_and_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = QueueServiceHttpAdapter(base_url="http://queue.local/", timeout_sec=2.0)
    with pytest.raises(ValueError, match="job_id is required"):
        _run(adapter.publish("   "))

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(post=_FakeResponse(status_code=200, json_data={"job_id": "6"})),
    )
    _run(adapter.publish("6"))


def test_queue_http_publish_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = QueueServiceHttpAdapter(base_url="http://queue.local", timeout_sec=2.0)
    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(RuntimeError, match="Queue publish failed"):
        _run(adapter.publish("6"))

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(post=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(RuntimeError, match="Queue publish failed"):
        _run(adapter.publish("6"))


def test_queue_http_consume_success_and_empty_payload_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = QueueServiceHttpAdapter(base_url="http://queue.local", timeout_sec=2.0)
    captured: dict[str, Any] = {}

    def _make_client(*args, **kwargs):
        client = _FakeAsyncClient(get=_FakeResponse(status_code=200, json_data={"job_id": " 7 "}))
        original_get = client.get

        async def _get(url: str, **kw):
            captured["params"] = kw.get("params")
            return await original_get(url, **kw)

        client.get = _get  # type: ignore[assignment]
        return client

    monkeypatch.setattr("ml_service.adapters.queue.http_queue.httpx.AsyncClient", _make_client)
    value = _run(adapter.consume(timeout=0.2))
    assert value == "7"
    assert float(captured["params"]["timeout_sec"]) == 0.2

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, json_data=["bad"])),
    )
    assert _run(adapter.consume(timeout=0.1)) is None

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, json_data={})),
    )
    assert _run(adapter.consume(timeout=0.1)) is None

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, json_data={"job_id": "  "})),
    )
    assert _run(adapter.consume(timeout=0.1)) is None


def test_queue_http_consume_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = QueueServiceHttpAdapter(base_url="http://queue.local", timeout_sec=2.0)
    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(error=httpx.HTTPError("boom")),
    )
    with pytest.raises(RuntimeError, match="Queue consume failed"):
        _run(adapter.consume(timeout=0.1))

    monkeypatch.setattr(
        "ml_service.adapters.queue.http_queue.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(RuntimeError, match="Queue consume failed"):
        _run(adapter.consume(timeout=0.1))


def test_minio_http_storage_save_upload_and_prepare_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage = MinioHttpFileStorage(base_url="http://minio.local/", base_dir=tmp_path, timeout_sec=2.0)
    monkeypatch.setattr(
        "ml_service.adapters.minio.http_storage.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(put=_FakeResponse(status_code=200)),
    )
    key = _run(storage.save_upload("6", "My Song.mp3", b"audio"))
    assert key == "uploads/6/My_Song.mp3"

    result_dir = _run(storage.prepare_results_dir("6"))
    assert result_dir.exists()
    assert result_dir == tmp_path / "results" / "6"


def test_minio_http_storage_save_upload_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage = MinioHttpFileStorage(base_url="http://minio.local", base_dir=tmp_path, timeout_sec=2.0)
    monkeypatch.setattr(
        "ml_service.adapters.minio.http_storage.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(put=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(RuntimeError, match="Failed to upload"):
        _run(storage.save_upload("6", "song.mp3", b"audio"))


def test_minio_http_storage_resolve_input_path_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage = MinioHttpFileStorage(base_url="http://minio.local", base_dir=tmp_path, timeout_sec=2.0)

    with pytest.raises(FileNotFoundError, match="Upload key is empty"):
        _run(storage.resolve_input_path("  "))

    cached = tmp_path / "minio-cache" / "uploads" / "6" / "song.mp3"
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(b"cached")
    assert _run(storage.resolve_input_path("uploads/6/song.mp3")) == cached

    if cached.exists():
        cached.unlink()

    monkeypatch.setattr(
        "ml_service.adapters.minio.http_storage.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=200, content=b"downloaded")),
    )
    path = _run(storage.resolve_input_path("uploads/6/song.mp3"))
    assert path.exists()
    assert path.read_bytes() == b"downloaded"

    monkeypatch.setattr(
        "ml_service.adapters.minio.http_storage.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=404, text="missing")),
    )
    with pytest.raises(FileNotFoundError, match="Upload not found"):
        _run(storage.resolve_input_path("uploads/6/missing.mp3"))

    monkeypatch.setattr(
        "ml_service.adapters.minio.http_storage.httpx.AsyncClient",
        lambda *args, **kwargs: _FakeAsyncClient(get=_FakeResponse(status_code=500, text="err")),
    )
    with pytest.raises(RuntimeError, match="Failed to download"):
        _run(storage.resolve_input_path("uploads/6/missing.mp3"))

