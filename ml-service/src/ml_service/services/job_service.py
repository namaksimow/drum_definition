from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from ml_service.domain.audio_pipeline import analyze_audio_file
from ml_service.domain.models import Job
from ml_service.domain.tablature import build_tablature_data, format_ascii_from_tablature, save_tablature_json
from ml_service.domain.tablature_report import save_ascii_tab_report
from ml_service.ports.file_storage import FileStorage
from ml_service.ports.job_repo import JobRepo
from ml_service.ports.queue import JobQueue


class JobService:
    def __init__(self, repo: JobRepo, storage: FileStorage, queue: JobQueue) -> None:
        self.repo = repo
        self.storage = storage
        self.queue = queue

    async def submit_job(self, *, filename: str, data: bytes) -> Job:
        job_id = str(uuid.uuid4())
        input_key = await self.storage.save_upload(job_id, filename, data)
        job = Job(
            id=job_id,
            filename=filename,
            input_key=input_key,
            status="queued",
        )
        await self.repo.create(job)
        await self.queue.publish(job_id)
        return job

    async def get_job(self, job_id: str) -> Job | None:
        return await self.repo.get(job_id)

    async def process_job(self, job_id: str) -> Job | None:
        job = await self.repo.get(job_id)
        if job is None:
            return None

        await self.repo.update(job_id, status="processing", error=None)
        try:
            input_path = await self.storage.resolve_input_path(job.input_key)
            result_dir = await self.storage.prepare_results_dir(job_id)
            manifest = self._run_pipeline(input_path=input_path, result_dir=result_dir)
            updated = await self.repo.update(job_id, status="done", result_manifest=manifest, error=None)
            return updated
        except Exception as exc:  # noqa: BLE001
            return await self.repo.update(job_id, status="failed", error=str(exc))

    async def run_worker_loop(self, *, stop_event: asyncio.Event, poll_timeout_sec: float = 1.0) -> None:
        while not stop_event.is_set():
            job_id = await self.queue.consume(timeout=poll_timeout_sec)
            if job_id is None:
                continue
            await self.process_job(job_id)

    def _run_pipeline(self, *, input_path: Path, result_dir: Path) -> dict:
        pipeline_result = analyze_audio_file(
            audio_path=input_path,
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
        tab_text = format_ascii_from_tablature(tab_data)

        tablature_json_path = result_dir / "tablature.json"
        tab_png_path = result_dir / "ascii_tab_report.png"
        tab_pdf_path = result_dir / "ascii_tab_report.pdf"

        save_tablature_json(tab_data, str(tablature_json_path))
        save_ascii_tab_report(tab_text, str(tab_png_path))
        save_ascii_tab_report(tab_text, str(tab_pdf_path))

        return {
            "input_file": str(input_path),
            "output_dir": str(result_dir),
            "tempo_bpm": pipeline_result["tempo_bpm"],
            "analysis_start_sec": pipeline_result["analysis_start_sec"],
            "analysis_end_sec": pipeline_result["analysis_end_sec"],
            "parts": pipeline_result["parts"],
            "tablature": {
                "json": str(tablature_json_path),
                "png": str(tab_png_path),
                "pdf": str(tab_pdf_path),
            },
        }

