from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ml_service.bootstrap import get_container

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.post("/jobs")
async def create_job(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(default=None),
    tablature_name: Optional[str] = Form(default=None),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if not file.filename.lower().endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only .mp3 files are supported")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File is empty")

    container = get_container()
    job = await container.job_service.submit_job(
        filename=file.filename,
        data=data,
        owner_user_id=user_id,
        tablature_name=tablature_name,
    )
    return {"job": job.to_dict()}


@router.get("/jobs")
async def list_jobs() -> dict:
    container = get_container()
    jobs = await container.job_service.list_jobs()
    return {
        "count": len(jobs),
        "job_ids": [job.id for job in jobs],
        "jobs": [job.to_dict() for job in jobs],
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    container = get_container()
    job = await container.job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job.to_dict()}


@router.get("/jobs/{job_id}/tablature")
async def get_job_tablature(job_id: str) -> dict:
    container = get_container()
    job = await container.job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done":
        raise HTTPException(status_code=409, detail=f"Job is not ready yet. Current status: {job.status}")

    tablature = await container.job_service.get_tablature(job_id)
    if tablature is None:
        raise HTTPException(status_code=404, detail="Tablature not found")

    return {"job_id": job_id, "tablature": tablature}


@router.get("/jobs/{job_id}/pdf")
async def get_job_pdf(job_id: str) -> FileResponse:
    container = get_container()
    job = await container.job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done":
        raise HTTPException(status_code=409, detail=f"Job is not ready yet. Current status: {job.status}")

    pdf_path = await container.job_service.generate_pdf(job_id)
    if pdf_path is None or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{job_id}.pdf",
    )


@router.get("/songs")
async def list_songs() -> dict:
    container = get_container()
    songs_dir = container.settings.songs_dir
    songs_dir.mkdir(parents=True, exist_ok=True)

    songs = sorted(
        p.name
        for p in songs_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".mp3", ".wav"}
    )
    return {"songs_dir": str(songs_dir), "songs": songs}


@router.post("/jobs/from-songs/{song_name}")
async def create_job_from_songs(song_name: str) -> dict:
    container = get_container()

    if Path(song_name).name != song_name:
        raise HTTPException(status_code=400, detail="Invalid song name")

    song_path = container.settings.songs_dir / song_name
    if not song_path.exists():
        raise HTTPException(status_code=404, detail="Song file not found in songs directory")

    if song_path.suffix.lower() not in {".mp3", ".wav"}:
        raise HTTPException(status_code=400, detail="Only .mp3/.wav files are supported")

    job = await container.job_service.submit_job_from_path(song_path=song_path)
    return {"job": job.to_dict()}
