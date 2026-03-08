from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from backend_app.bootstrap import Container
from backend_app.presentation.http.error_mapper import to_http_exception


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=256)
    nickname: str = Field(min_length=1, max_length=64)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UpdateMeRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)


class UpdatePersonalTablatureRequest(BaseModel):
    track_file_name: Optional[str] = Field(default=None, max_length=255)
    visibility: Optional[str] = Field(default=None, max_length=64)
    json_format: Optional[dict] = None


class CreatePublicCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SetPublicReactionRequest(BaseModel):
    reaction_type: str = Field(min_length=1, max_length=32)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


def build_router(container: Container) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def index() -> FileResponse:
        try:
            index_path = container.get_index_page.execute()
            return FileResponse(index_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/community/tablatures/{tablature_id}")
    async def community_tablature_page(tablature_id: int) -> FileResponse:
        _ = tablature_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "community_tablature.html"
            return FileResponse(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/account")
    async def account_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "account.html"
            return FileResponse(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/create")
    async def create_tablature_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "create_tablature.html"
            return FileResponse(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/edit")
    async def edit_tablature_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "edit_tablatures.html"
            return FileResponse(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/edit/tablature/{tablature_id}")
    async def edit_tablature_detail_page(tablature_id: int) -> FileResponse:
        _ = tablature_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "edit_tablature_detail.html"
            return FileResponse(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/upload")
    async def upload_file(
        file: UploadFile = File(...),
        authorization: Optional[str] = Header(default=None),
        tablature_name: Optional[str] = Form(default=None),
    ) -> dict:
        try:
            user_id: int | None = None
            if authorization:
                token = _extract_bearer_token(authorization)
                user = await container.get_current_user.execute(token=token)
                user_id = int(user["id"])

            data = await file.read()
            uploaded = await container.upload_audio.execute(
                filename=file.filename,
                data=data,
                content_type=file.content_type or "application/octet-stream",
                user_id=user_id,
                tablature_name=tablature_name,
            )
            return uploaded.raw_payload
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/pdf")
    async def get_pdf(job_id: str = Query(..., min_length=1)) -> Response:
        try:
            artifact = await container.get_pdf_by_job_id.execute(job_id=job_id)
            return Response(
                content=artifact.content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{artifact.download_filename}"'
                },
            )
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        try:
            job = await container.get_job_by_id.execute(job_id=job_id)
            return {"job": {"id": job.id, "status": job.status}}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/tablature")
    async def get_tablature(job_id: str = Query(..., min_length=1)) -> dict:
        try:
            artifact = await container.get_tablature_by_job_id.execute(job_id=job_id)
            return {"job_id": artifact.job_id, "tablature": artifact.tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/tablatures")
    async def list_public_tablatures(
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            items = await container.list_public_tablatures.execute(query=q, limit=limit, offset=offset)
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "task_id": item.task_id,
                        "track_file_name": item.track_file_name,
                        "author": item.author,
                        "result_path": item.result_path,
                        "created_at": item.created_at,
                        "comments_count": item.comments_count,
                        "reactions_like_count": item.reactions_like_count,
                        "reactions_fire_count": item.reactions_fire_count,
                        "reactions_wow_count": item.reactions_wow_count,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/personal/tablatures")
    async def list_personal_tablatures(
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_personal_tablatures.execute(
                token=token,
                query=q,
                limit=limit,
                offset=offset,
            )
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "task_id": item.task_id,
                        "track_file_name": item.track_file_name,
                        "author": item.author,
                        "result_path": item.result_path,
                        "created_at": item.created_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/personal/tablatures/{tablature_id}")
    async def get_personal_tablature(
        tablature_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            tablature = await container.get_personal_tablature_by_id.execute(
                token=token,
                tablature_id=tablature_id,
            )
            return {"tablature": tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/personal/tablatures/{tablature_id}")
    async def patch_personal_tablature(
        tablature_id: int,
        payload: UpdatePersonalTablatureRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            tablature = await container.update_personal_tablature.execute(
                token=token,
                tablature_id=tablature_id,
                track_file_name=payload.track_file_name,
                visibility=payload.visibility,
                json_format=payload.json_format,
            )
            return {"tablature": tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/tablatures/{tablature_id}")
    async def get_public_tablature(tablature_id: int) -> dict:
        try:
            tablature = await container.get_public_tablature_by_id.execute(tablature_id=tablature_id)
            return {"tablature": tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/tablatures/{tablature_id}/comments")
    async def list_public_tablature_comments(
        tablature_id: int,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            items = await container.list_public_tablature_comments.execute(
                tablature_id=tablature_id,
                limit=limit,
                offset=offset,
            )
            return {"count": len(items), "items": items}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/community/tablatures/{tablature_id}/comments")
    async def create_public_tablature_comment(
        tablature_id: int,
        payload: CreatePublicCommentRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            comment = await container.create_public_tablature_comment.execute(
                token=token,
                tablature_id=tablature_id,
                content=payload.content,
            )
            return {"comment": comment}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/tablatures/{tablature_id}/reactions")
    async def get_public_tablature_reactions(
        tablature_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token: str | None = None
            if authorization:
                token = _extract_bearer_token(authorization)
            reactions = await container.get_public_tablature_reactions.execute(
                tablature_id=tablature_id,
                token=token,
            )
            return {"reactions": reactions}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/community/tablatures/{tablature_id}/reactions")
    async def set_public_tablature_reaction(
        tablature_id: int,
        payload: SetPublicReactionRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            reactions = await container.set_public_tablature_reaction.execute(
                token=token,
                tablature_id=tablature_id,
                reaction_type=payload.reaction_type,
            )
            return {"reactions": reactions}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/tablatures/{tablature_id}/download")
    async def download_public_tablature_json(tablature_id: int) -> Response:
        try:
            artifact = await container.download_public_tablature_json.execute(tablature_id=tablature_id)
            return Response(
                content=artifact.content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{artifact.download_filename}"'
                },
            )
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/auth/register")
    async def register_user(payload: RegisterRequest) -> dict:
        try:
            user = await container.register_user.execute(
                email=payload.email,
                password=payload.password,
                nickname=payload.nickname,
            )
            return {"user": user}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/auth/login")
    async def login_user(payload: LoginRequest) -> dict:
        try:
            return await container.login_user.execute(
                email=payload.email,
                password=payload.password,
            )
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/auth/me")
    async def auth_me(authorization: Optional[str] = Header(default=None)) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            user = await container.get_current_user.execute(token=token)
            return {"user": user}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/auth/me")
    async def patch_auth_me(payload: UpdateMeRequest, authorization: Optional[str] = Header(default=None)) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            user = await container.update_current_user.execute(token=token, nickname=payload.nickname)
            return {"user": user}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return router
