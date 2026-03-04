from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from backend_app.bootstrap import Container
from backend_app.presentation.http.error_mapper import to_http_exception


def build_router(container: Container) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def index() -> FileResponse:
        try:
            index_path = container.get_index_page.execute()
            return FileResponse(index_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)) -> dict:
        try:
            data = await file.read()
            uploaded = await container.upload_audio.execute(
                filename=file.filename,
                data=data,
                content_type=file.content_type or "application/octet-stream",
            )
            return uploaded.raw_payload
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/pdf")
    async def get_pdf(job_id: str = Query(..., min_length=1)) -> FileResponse:
        try:
            artifact = await container.get_pdf_by_job_id.execute(job_id=job_id)
            return FileResponse(
                artifact.file_path,
                media_type="application/pdf",
                filename=artifact.download_filename,
            )
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return router

