from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from ml_service.domain.audio_pipeline import run_song_pipeline
from ml_service.domain.models import Job
from ml_service.domain.tablature import build_tablature_data, format_ascii_from_tablature, save_tablature_json
from ml_service.domain.tablature_report import save_ascii_tab_report
from ml_service.ports.file_storage import FileStorage
from ml_service.ports.job_repo import JobRepo
from ml_service.ports.queue import JobQueue
from ml_service.ports.tablature_store import TablatureStore


class JobService:
    def __init__(self, repo: JobRepo, storage: FileStorage, queue: JobQueue, tablature_store: TablatureStore) -> None:
        self.repo = repo
        self.storage = storage
        self.queue = queue
        self.tablature_store = tablature_store

    async def submit_job(
        self,
        *,
        filename: str,
        data: bytes,
        owner_user_id: int | None = None,
        tablature_name: str | None = None,
    ) -> Job:
        job_id = str(uuid.uuid4())
        input_key = await self.storage.save_upload(job_id, filename, data)
        job = Job(
            id=job_id,
            filename=filename,
            input_key=input_key,
            status="queued",
        )
        if owner_user_id is not None:
            job.result_manifest["owner_user_id"] = int(owner_user_id)
        await self.repo.create(
            job,
            owner_user_id=owner_user_id,
            track_title=tablature_name,
        )
        await self.queue.publish(job.id)
        return job

    async def get_job(self, job_id: str) -> Job | None:
        return await self.repo.get(job_id)

    async def get_tablature(self, job_id: str) -> dict | None:
        tablature = await self.tablature_store.get(job_id)
        if tablature is not None:
            return tablature

        # Fallback for older jobs: read file path from manifest if present.
        job = await self.repo.get(job_id)
        if job is None:
            return None

        json_path = (
            job.result_manifest.get("tablature", {})
            .get("json")
        )
        if not json_path:
            return None

        path = Path(str(json_path))
        if not path.exists():
            return None

        return json.loads(path.read_text(encoding="utf-8"))

    async def generate_pdf(self, job_id: str) -> Path | None:
        job = await self.repo.get(job_id)
        if job is None:
            return None

        tablature = await self.get_tablature(job_id)
        if tablature is None:
            return None

        result_dir_raw = job.result_manifest.get("output_dir")
        if result_dir_raw:
            result_dir = Path(str(result_dir_raw))
            result_dir.mkdir(parents=True, exist_ok=True)
        else:
            result_dir = await self.storage.prepare_results_dir(job_id)

        tab_text = format_ascii_from_tablature(tablature)
        pdf_path = result_dir / "ascii_tab_report.pdf"
        save_ascii_tab_report(tab_text, str(pdf_path))

        manifest = dict(job.result_manifest)
        tablature_manifest = dict(manifest.get("tablature") or {})
        tablature_manifest["pdf"] = str(pdf_path)
        manifest["tablature"] = tablature_manifest
        await self.repo.update(job_id, result_manifest=manifest)
        return pdf_path

    async def list_jobs(self) -> list[Job]:
        return await self.repo.list()

    async def submit_job_from_path(self, song_path: Path) -> Job:
        if not song_path.exists():
            raise FileNotFoundError(f"Song file not found: {song_path}")

        data = song_path.read_bytes()
        return await self.submit_job(filename=song_path.name, data=data)

    async def process_job(self, job_id: str) -> Job | None:
        job = await self.repo.get(job_id)
        if job is None:
            return None

        await self.repo.update(job_id, status="processing", error=None)
        try:
            input_path = await self.storage.resolve_input_path(job.input_key)
            result_dir = await self.storage.prepare_results_dir(job_id)
            pipeline_output = self._run_pipeline(input_path=input_path, result_dir=result_dir)
            tablature_data = pipeline_output.pop("_tablature_data", None)
            if isinstance(tablature_data, dict):
                await self.tablature_store.save(job_id, tablature_data)
            manifest = pipeline_output
            updated = await self.repo.update(job_id, status="done", result_manifest=manifest, error=None)
            return updated
        except Exception as exc:  # noqa: BLE001
            return await self.repo.update(job_id, status="failed", error=str(exc))

    async def run_worker_loop(self, *, stop_event: asyncio.Event, poll_timeout_sec: float = 1.0) -> None:
        while not stop_event.is_set():
            try:
                job_id = await self.queue.consume(timeout=poll_timeout_sec)
            except Exception:  # noqa: BLE001
                await asyncio.sleep(min(max(poll_timeout_sec, 0.1), 2.0))
                continue
            if job_id is None:
                continue
            try:
                await self.process_job(job_id)
            except Exception:  # noqa: BLE001
                continue

    def _run_pipeline(self, *, input_path: Path, result_dir: Path) -> dict:
        pipeline_result = run_song_pipeline(
            song_path=input_path,
            output_dir=result_dir,
            start_time=0.0,
            duration=None,
            plot=True,
            plot_chunk_sec=8.0,
        )

        tab_data = build_tablature_data(
            beat_times=pipeline_result["beat_times_sec"],
            events=pipeline_result["events"],
            start_time=pipeline_result["analysis_start_sec"],
            end_time=pipeline_result["analysis_end_sec"],
            beats_per_bar=4,
            subdivisions=4,
            bars_per_line=4,
        )

        tablature_json_path = result_dir / "tablature.json"

        save_tablature_json(tab_data, str(tablature_json_path))

        return {
            "input_song": str(input_path),
            "output_dir": str(result_dir),
            "tempo_bpm": pipeline_result["tempo_bpm"],
            "stems": pipeline_result["stems"],
            "drums_stem": pipeline_result["drums_stem"],
            "analysis_start_sec": pipeline_result["analysis_start_sec"],
            "analysis_end_sec": pipeline_result["analysis_end_sec"],
            "parts": pipeline_result["parts"],
            "tablature": {
                "json": str(tablature_json_path),
            },
            "_tablature_data": tab_data,
        }
