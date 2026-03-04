from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ml_service.bootstrap import get_container

router = APIRouter(prefix="/v1", tags=["jobs"])


@router.post("/jobs")
async def create_job(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="File is empty")

    container = get_container()
    job = await container.job_service.submit_job(filename=file.filename, data=data)
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
