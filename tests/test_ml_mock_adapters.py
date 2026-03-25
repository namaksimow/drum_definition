from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ml_service.adapters.mock.mock_queue import MockQueue
from ml_service.adapters.mock.mock_storage import MockFileStorage


def test_mock_queue_publish_then_consume_returns_same_job_id() -> None:
    async def _scenario() -> str | None:
        queue = MockQueue()
        await queue.publish("123")
        return await queue.consume(timeout=0.1)

    consumed = asyncio.run(_scenario())
    assert consumed == "123"


def test_mock_queue_consume_timeout_returns_none() -> None:
    async def _scenario() -> str | None:
        queue = MockQueue()
        return await queue.consume(timeout=0.01)

    consumed = asyncio.run(_scenario())
    assert consumed is None


def test_mock_storage_round_trip(tmp_path: Path) -> None:
    storage = MockFileStorage(base_dir=tmp_path)

    async def _scenario() -> tuple[str, bytes]:
        key = await storage.save_upload("job-1", "My Song.mp3", b"payload")
        resolved = await storage.resolve_input_path(key)
        return key, resolved.read_bytes()

    key, content = asyncio.run(_scenario())
    assert key.endswith("_My_Song.mp3")
    assert content == b"payload"


def test_mock_storage_raises_for_missing_key(tmp_path: Path) -> None:
    storage = MockFileStorage(base_dir=tmp_path)

    with pytest.raises(FileNotFoundError, match="Upload not found"):
        asyncio.run(storage.resolve_input_path("missing.mp3"))
