from __future__ import annotations

import asyncio

from ml_service.adapters.mock.mock_job_repo import MockJobRepo
from ml_service.adapters.mock.mock_tablature_store import MockTablatureStore
from ml_service.domain.models import Job


def test_mock_job_repo_create_get_list_update() -> None:
    async def _scenario():
        repo = MockJobRepo()
        job = Job(id="1", filename="song.mp3", input_key="k", status="queued")
        await repo.create(job, owner_user_id=1, track_title="Song")
        loaded = await repo.get("1")
        assert loaded is not None
        assert loaded.id == "1"

        listed = await repo.list()
        assert len(listed) == 1
        assert listed[0].id == "1"

        updated = await repo.update("1", status="done", result_manifest={"a": 1}, error=None)
        assert updated is not None
        assert updated.status == "done"
        assert updated.result_manifest == {"a": 1}

        missing = await repo.update("404", status="failed", result_manifest={}, error="x")
        assert missing is None

    asyncio.run(_scenario())


def test_mock_tablature_store_save_and_get() -> None:
    async def _scenario():
        store = MockTablatureStore()
        assert await store.get("1") is None
        payload = {"meta": {"tempo": 120}, "lines": []}
        await store.save("1", payload)
        assert await store.get("1") == payload

    asyncio.run(_scenario())

