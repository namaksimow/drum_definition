from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from ml_service.domain.models import Job


# JobService imports audio_pipeline (librosa/spleeter path). For unit-tests we stub this module.
if "ml_service.domain.audio_pipeline" not in sys.modules:
    _audio_pipeline_stub = types.ModuleType("ml_service.domain.audio_pipeline")

    def _run_song_pipeline_stub(*args, **kwargs):
        raise RuntimeError("run_song_pipeline stub should be overridden in tests")

    _audio_pipeline_stub.run_song_pipeline = _run_song_pipeline_stub
    sys.modules["ml_service.domain.audio_pipeline"] = _audio_pipeline_stub

from ml_service.services.job_service import JobService


class _RepoStub:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.create_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []
        self.list_items: list[Job] = []
        self.force_created_id: str | None = None

    async def create(self, job: Job, *, owner_user_id: int | None = None, track_title: str | None = None) -> None:
        self.create_calls.append(
            {
                "job_id": job.id,
                "owner_user_id": owner_user_id,
                "track_title": track_title,
            }
        )
        if self.force_created_id is not None:
            job.id = self.force_created_id
        self.jobs[job.id] = job

    async def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    async def list(self) -> list[Job]:
        if self.list_items:
            return list(self.list_items)
        return list(self.jobs.values())

    async def update(
        self,
        job_id: str,
        *,
        status: str | None = None,
        result_manifest: dict | None = None,
        error: str | None = None,
    ) -> Job | None:
        self.update_calls.append(
            {
                "job_id": job_id,
                "status": status,
                "result_manifest": result_manifest,
                "error": error,
            }
        )
        job = self.jobs.get(job_id)
        if job is None:
            return None
        if status is not None:
            job.status = status  # type: ignore[assignment]
        if result_manifest is not None:
            job.result_manifest = result_manifest
        job.error = error
        return job


class _StorageStub:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.upload_calls: list[dict[str, Any]] = []
        self.resolve_calls: list[str] = []
        self.prepare_calls: list[str] = []

    async def save_upload(self, job_id: str, filename: str, data: bytes) -> str:
        self.upload_calls.append({"job_id": job_id, "filename": filename, "size": len(data)})
        key = f"{job_id}_{filename}"
        target = self.base_dir / "uploads" / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return key

    async def resolve_input_path(self, input_key: str) -> Path:
        self.resolve_calls.append(input_key)
        path = self.base_dir / "uploads" / input_key
        if not path.exists():
            raise FileNotFoundError(input_key)
        return path

    async def prepare_results_dir(self, job_id: str) -> Path:
        self.prepare_calls.append(job_id)
        path = self.base_dir / "results" / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path


class _QueueStub:
    def __init__(self) -> None:
        self.published: list[str] = []
        self.to_consume: list[str | None] = []
        self.raise_on_consume = False

    async def publish(self, job_id: str) -> None:
        self.published.append(job_id)

    async def consume(self, timeout: float | None = None) -> str | None:
        if self.raise_on_consume:
            raise RuntimeError("consume failed")
        if self.to_consume:
            return self.to_consume.pop(0)
        if timeout is not None and timeout > 0:
            await asyncio.sleep(timeout)
            return None
        return None


class _TablatureStoreStub:
    def __init__(self) -> None:
        self.data: dict[str, dict] = {}
        self.saved: list[tuple[str, dict]] = []

    async def save(self, job_id: str, tablature: dict) -> None:
        self.saved.append((job_id, tablature))
        self.data[job_id] = tablature

    async def get(self, job_id: str) -> dict | None:
        return self.data.get(job_id)


def _build_service(tmp_path: Path) -> tuple[JobService, _RepoStub, _StorageStub, _QueueStub, _TablatureStoreStub]:
    repo = _RepoStub()
    storage = _StorageStub(tmp_path)
    queue = _QueueStub()
    store = _TablatureStoreStub()
    return JobService(repo=repo, storage=storage, queue=queue, tablature_store=store), repo, storage, queue, store


def test_submit_job_saves_upload_persists_and_publishes(tmp_path: Path) -> None:
    service, repo, storage, queue, _ = _build_service(tmp_path)
    repo.force_created_id = "10"

    job = asyncio.run(
        service.submit_job(
            filename="track.mp3",
            data=b"audio-bytes",
            owner_user_id=5,
            tablature_name="My Song",
        )
    )

    assert job.id == "10"
    assert storage.upload_calls
    assert queue.published == ["10"]
    assert repo.create_calls[0]["owner_user_id"] == 5
    assert repo.create_calls[0]["track_title"] == "My Song"


def test_get_tablature_returns_store_value_first(tmp_path: Path) -> None:
    service, _, _, _, store = _build_service(tmp_path)
    store.data["6"] = {"meta": {}, "lines": []}
    result = asyncio.run(service.get_tablature("6"))
    assert result == {"meta": {}, "lines": []}


def test_get_tablature_fallback_reads_json_path_from_manifest(tmp_path: Path) -> None:
    service, repo, _, _, _ = _build_service(tmp_path)
    payload = {"meta": {"tempo": 120}, "lines": []}
    json_path = tmp_path / "result" / "tablature.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    repo.jobs["6"] = Job(
        id="6",
        filename="track.mp3",
        input_key="key",
        status="done",
        result_manifest={"tablature": {"json": str(json_path)}},
    )

    result = asyncio.run(service.get_tablature("6"))
    assert result == payload


def test_get_tablature_returns_none_for_missing_job(tmp_path: Path) -> None:
    service, _, _, _, _ = _build_service(tmp_path)
    assert asyncio.run(service.get_tablature("404")) is None


def test_generate_pdf_returns_none_if_job_missing(tmp_path: Path) -> None:
    service, _, _, _, _ = _build_service(tmp_path)
    assert asyncio.run(service.generate_pdf("404")) is None


def test_generate_pdf_returns_none_if_tablature_missing(tmp_path: Path) -> None:
    service, repo, _, _, _ = _build_service(tmp_path)
    repo.jobs["6"] = Job(id="6", filename="track.mp3", input_key="k", status="done")
    assert asyncio.run(service.generate_pdf("6")) is None


def test_generate_pdf_writes_manifest_with_pdf_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, _, _, store = _build_service(tmp_path)
    output_dir = tmp_path / "out" / "6"
    repo.jobs["6"] = Job(
        id="6",
        filename="track.mp3",
        input_key="k",
        status="done",
        result_manifest={"output_dir": str(output_dir), "tablature": {"json": "ignored"}},
    )
    store.data["6"] = {"lines": []}

    def _fake_save_ascii(text: str, out_path: str) -> None:
        Path(out_path).write_bytes(b"%PDF")

    monkeypatch.setattr("ml_service.services.job_service.save_ascii_tab_report", _fake_save_ascii)

    pdf_path = asyncio.run(service.generate_pdf("6"))
    assert pdf_path is not None
    assert pdf_path.exists()
    assert repo.update_calls
    manifest = repo.update_calls[-1]["result_manifest"]
    assert manifest is not None
    assert "pdf" in manifest["tablature"]


def test_generate_pdf_uses_prepare_results_dir_without_output_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, storage, _, store = _build_service(tmp_path)
    repo.jobs["7"] = Job(id="7", filename="track.mp3", input_key="k", status="done", result_manifest={})
    store.data["7"] = {"lines": []}

    def _fake_save_ascii(text: str, out_path: str) -> None:
        Path(out_path).write_bytes(b"%PDF")

    monkeypatch.setattr("ml_service.services.job_service.save_ascii_tab_report", _fake_save_ascii)
    pdf_path = asyncio.run(service.generate_pdf("7"))
    assert pdf_path is not None
    assert storage.prepare_calls == ["7"]


def test_process_job_returns_none_if_not_found(tmp_path: Path) -> None:
    service, _, _, _, _ = _build_service(tmp_path)
    assert asyncio.run(service.process_job("404")) is None


def test_process_job_success_updates_status_and_saves_tablature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, storage, _, store = _build_service(tmp_path)
    repo.jobs["6"] = Job(id="6", filename="track.mp3", input_key="6_track.mp3", status="queued")
    upload_path = tmp_path / "uploads" / "6_track.mp3"
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_bytes(b"audio")

    def _fake_pipeline(*, input_path: Path, result_dir: Path) -> dict:
        assert input_path.exists()
        assert result_dir.exists()
        return {
            "tempo_bpm": 120.0,
            "stems": {},
            "drums_stem": "d",
            "analysis_start_sec": 0.0,
            "analysis_end_sec": 1.0,
            "parts": {},
            "tablature": {"json": str(result_dir / "tablature.json")},
            "_tablature_data": {"meta": {}, "lines": []},
        }

    monkeypatch.setattr(service, "_run_pipeline", _fake_pipeline)
    result = asyncio.run(service.process_job("6"))

    assert result is not None
    assert result.status == "done"
    assert store.saved and store.saved[0][0] == "6"
    statuses = [c["status"] for c in repo.update_calls]
    assert statuses[0] == "processing"
    assert statuses[-1] == "done"


def test_process_job_without_dict_tablature_data_does_not_save_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, _, _, store = _build_service(tmp_path)
    repo.jobs["6"] = Job(id="6", filename="track.mp3", input_key="6_track.mp3", status="queued")
    (tmp_path / "uploads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "uploads" / "6_track.mp3").write_bytes(b"audio")

    def _fake_pipeline(*, input_path: Path, result_dir: Path) -> dict:
        return {
            "tempo_bpm": 120.0,
            "stems": {},
            "drums_stem": "d",
            "analysis_start_sec": 0.0,
            "analysis_end_sec": 1.0,
            "parts": {},
            "tablature": {"json": str(result_dir / "tablature.json")},
            "_tablature_data": "not-a-dict",
        }

    monkeypatch.setattr(service, "_run_pipeline", _fake_pipeline)
    result = asyncio.run(service.process_job("6"))
    assert result is not None
    assert result.status == "done"
    assert store.saved == []


def test_process_job_failure_sets_failed_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, repo, _, _, _ = _build_service(tmp_path)
    repo.jobs["6"] = Job(id="6", filename="track.mp3", input_key="6_track.mp3", status="queued")
    (tmp_path / "uploads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "uploads" / "6_track.mp3").write_bytes(b"audio")

    def _boom(*, input_path: Path, result_dir: Path) -> dict:
        raise RuntimeError("pipeline exploded")

    monkeypatch.setattr(service, "_run_pipeline", _boom)
    result = asyncio.run(service.process_job("6"))
    assert result is not None
    assert result.status == "failed"
    assert "pipeline exploded" in str(result.error)


def test_run_worker_loop_processes_one_job_and_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, _, queue, _ = _build_service(tmp_path)
    queue.to_consume.append("6")

    calls: list[str] = []

    async def _scenario() -> None:
        stop_event = asyncio.Event()

        async def _fake_process(job_id: str):
            calls.append(job_id)
            stop_event.set()
            return None

        monkeypatch.setattr(service, "process_job", _fake_process)
        await service.run_worker_loop(stop_event=stop_event, poll_timeout_sec=0.01)

    asyncio.run(_scenario())
    assert calls == ["6"]


def test_run_worker_loop_tolerates_consume_errors(tmp_path: Path) -> None:
    service, _, _, queue, _ = _build_service(tmp_path)
    queue.raise_on_consume = True

    async def _scenario() -> None:
        stop_event = asyncio.Event()
        task = asyncio.create_task(service.run_worker_loop(stop_event=stop_event, poll_timeout_sec=0.01))
        await asyncio.sleep(0.03)
        stop_event.set()
        await task

    asyncio.run(_scenario())


def test_submit_job_from_path_raises_if_file_missing(tmp_path: Path) -> None:
    service, _, _, _, _ = _build_service(tmp_path)
    with pytest.raises(FileNotFoundError):
        asyncio.run(service.submit_job_from_path(tmp_path / "missing.mp3"))


def test_submit_job_from_path_reads_file_and_delegates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service, _, _, _, _ = _build_service(tmp_path)
    song = tmp_path / "song.mp3"
    song.write_bytes(b"audio-data")

    captured: dict[str, Any] = {}

    async def _fake_submit_job(*, filename: str, data: bytes, owner_user_id=None, tablature_name=None):
        captured["filename"] = filename
        captured["data"] = data
        return Job(id="x", filename=filename, input_key="k", status="queued")

    monkeypatch.setattr(service, "submit_job", _fake_submit_job)
    job = asyncio.run(service.submit_job_from_path(song_path=song))
    assert job.id == "x"
    assert captured["filename"] == "song.mp3"
    assert captured["data"] == b"audio-data"
