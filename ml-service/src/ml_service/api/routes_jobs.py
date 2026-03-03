from __future__ import annotations

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


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    container = get_container()
    job = await container.job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job.to_dict()}

