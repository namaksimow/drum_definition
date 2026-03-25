from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import types
import io
import asyncio

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile
import pytest

# routes_jobs imports bootstrap -> job_service -> audio_pipeline (librosa/spleeter).
# Stub audio_pipeline module for unit-test environment.
if "ml_service.domain.audio_pipeline" not in sys.modules:
    _audio_pipeline_stub = types.ModuleType("ml_service.domain.audio_pipeline")

    def _run_song_pipeline_stub(*args, **kwargs):
        raise RuntimeError("run_song_pipeline stub should not be used in route tests")

    _audio_pipeline_stub.run_song_pipeline = _run_song_pipeline_stub
    sys.modules["ml_service.domain.audio_pipeline"] = _audio_pipeline_stub

from ml_service.api.routes_jobs import router
from ml_service.domain.models import Job
import ml_service.api.routes_jobs as routes_jobs_module


class _JobServiceStub:
    def __init__(self) -> None:
        self.submit_job_result: Job | None = None
        self.list_jobs_result: list[Job] = []
        self.get_job_result: Job | None = None
        self.get_tablature_result: dict | None = None
        self.generate_pdf_result: Path | None = None
        self.submit_job_from_path_result: Job | None = None

    async def submit_job(self, **kwargs) -> Job:
        assert self.submit_job_result is not None
        return self.submit_job_result

    async def list_jobs(self) -> list[Job]:
        return self.list_jobs_result

    async def get_job(self, job_id: str) -> Job | None:
        return self.get_job_result

    async def get_tablature(self, job_id: str) -> dict | None:
        return self.get_tablature_result

    async def generate_pdf(self, job_id: str) -> Path | None:
        return self.generate_pdf_result

    async def submit_job_from_path(self, song_path: Path) -> Job:
        assert self.submit_job_from_path_result is not None
        return self.submit_job_from_path_result


def _build_client(tmp_path: Path) -> tuple[TestClient, _JobServiceStub]:
    app = FastAPI()
    app.include_router(router)
    service = _JobServiceStub()
    settings = SimpleNamespace(songs_dir=tmp_path / "songs")
    container = SimpleNamespace(job_service=service, settings=settings)

    import ml_service.api.routes_jobs as routes_jobs_module

    routes_jobs_module.get_container = lambda: container
    return TestClient(app), service


def test_create_job_validates_filename_extension_and_empty_payload(tmp_path: Path) -> None:
    client, _ = _build_client(tmp_path)

    r = client.post("/v1/jobs", files={"file": ("", b"abc", "audio/mpeg")})
    assert r.status_code == 422

    with pytest.raises(HTTPException, match="Filename is required"):
        upload = UploadFile(file=io.BytesIO(b"abc"), filename="")
        asyncio.run(routes_jobs_module.create_job(file=upload))

    r = client.post("/v1/jobs", files={"file": ("track.wav", b"abc", "audio/wav")})
    assert r.status_code == 400
    assert "Only .mp3 files are supported" in r.text

    r = client.post("/v1/jobs", files={"file": ("track.mp3", b"", "audio/mpeg")})
    assert r.status_code == 400
    assert "File is empty" in r.text


def test_create_job_and_list_jobs_success(tmp_path: Path) -> None:
    client, service = _build_client(tmp_path)
    service.submit_job_result = Job(id="6", filename="track.mp3", input_key="k", status="queued")
    service.list_jobs_result = [service.submit_job_result]

    r = client.post(
        "/v1/jobs",
        files={"file": ("track.mp3", b"abc", "audio/mpeg")},
        data={"user_id": "5", "tablature_name": "My Song"},
    )
    assert r.status_code == 200
    assert r.json()["job"]["id"] == "6"

    r = client.get("/v1/jobs")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["job_ids"] == ["6"]


def test_get_job_and_tablature_statuses(tmp_path: Path) -> None:
    client, service = _build_client(tmp_path)
    r = client.get("/v1/jobs/6")
    assert r.status_code == 404

    service.get_job_result = Job(id="6", filename="track.mp3", input_key="k", status="processing")
    r = client.get("/v1/jobs/6/tablature")
    assert r.status_code == 409

    service.get_job_result = Job(id="6", filename="track.mp3", input_key="k", status="done")
    service.get_tablature_result = None
    r = client.get("/v1/jobs/6/tablature")
    assert r.status_code == 404

    service.get_tablature_result = {"meta": {}, "lines": []}
    r = client.get("/v1/jobs/6/tablature")
    assert r.status_code == 200
    assert r.json()["job_id"] == "6"


def test_get_pdf_statuses_and_success(tmp_path: Path) -> None:
    client, service = _build_client(tmp_path)

    r = client.get("/v1/jobs/6/pdf")
    assert r.status_code == 404

    service.get_job_result = Job(id="6", filename="track.mp3", input_key="k", status="queued")
    r = client.get("/v1/jobs/6/pdf")
    assert r.status_code == 409

    service.get_job_result = Job(id="6", filename="track.mp3", input_key="k", status="done")
    service.generate_pdf_result = None
    r = client.get("/v1/jobs/6/pdf")
    assert r.status_code == 404

    pdf = tmp_path / "out.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.write_bytes(b"%PDF")
    service.generate_pdf_result = pdf
    r = client.get("/v1/jobs/6/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")


def test_songs_and_create_job_from_songs_paths(tmp_path: Path) -> None:
    client, service = _build_client(tmp_path)
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)
    (songs_dir / "a.mp3").write_bytes(b"1")
    (songs_dir / "b.wav").write_bytes(b"1")
    (songs_dir / "c.txt").write_text("x", encoding="utf-8")
    service.submit_job_from_path_result = Job(id="7", filename="a.mp3", input_key="k", status="queued")

    r = client.get("/v1/songs")
    assert r.status_code == 200
    assert r.json()["songs"] == ["a.mp3", "b.wav"]

    with pytest.raises(HTTPException, match="Invalid song name"):
        asyncio.run(routes_jobs_module.create_job_from_songs("a/../x.mp3"))

    r = client.post("/v1/jobs/from-songs/missing.mp3")
    assert r.status_code == 404

    r = client.post("/v1/jobs/from-songs/c.txt")
    assert r.status_code == 400

    r = client.post("/v1/jobs/from-songs/a.mp3")
    assert r.status_code == 200
    assert r.json()["job"]["id"] == "7"
