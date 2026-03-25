from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from uuid import uuid4

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


class CreateAuthorRoleRequestPayload(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class UpdateAdminAuthorRoleRequestPayload(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    admin_message: Optional[str] = Field(default=None, max_length=5000)


class UpdatePersonalTablatureRequest(BaseModel):
    track_file_name: Optional[str] = Field(default=None, max_length=255)
    visibility: Optional[str] = Field(default=None, max_length=64)
    json_format: Optional[dict] = None


class CreatePublicCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SetPublicReactionRequest(BaseModel):
    reaction_type: str = Field(min_length=1, max_length=32)


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    visibility: Optional[str] = Field(default="public", max_length=64)
    tags: List[str] = Field(default_factory=list)
    cover_image_path: Optional[str] = Field(default=None, max_length=1000)


class UpdatePersonalCourseRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    visibility: Optional[str] = Field(default=None, max_length=64)
    tags: Optional[List[str]] = None
    cover_image_path: Optional[str] = Field(default=None, max_length=1000)


class UpdateAdminVisibilityRequest(BaseModel):
    visibility: str = Field(min_length=1, max_length=64)


class UpdateAdminUserAccountRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=320)
    nickname: Optional[str] = Field(default=None, max_length=64)
    role: Optional[str] = Field(default=None, max_length=32)


class CreateCourseLessonRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: Optional[str] = Field(default="", max_length=20000)
    position: Optional[int] = Field(default=None, ge=1)


class UpdateCourseLessonRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = Field(default=None, max_length=20000)
    position: Optional[int] = Field(default=None, ge=1)


class SetLessonProgressRequest(BaseModel):
    completed: bool


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


def _html_file_response(path: Path) -> FileResponse:
    return FileResponse(
        path,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def build_router(container: Container) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    async def index() -> FileResponse:
        try:
            index_path = container.get_index_page.execute()
            return _html_file_response(index_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/community/tablatures/{tablature_id}")
    async def community_tablature_page(tablature_id: int) -> FileResponse:
        _ = tablature_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "community_tablature.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/account")
    async def account_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "account.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/admin")
    async def admin_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "admin.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/admin/console")
    async def admin_console_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "admin.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/create")
    async def create_tablature_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "create_tablature.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/auth")
    async def auth_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "auth.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/edit")
    async def edit_tablature_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "edit_tablatures.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/courses")
    async def courses_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "courses.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/courses/create")
    async def create_course_page() -> FileResponse:
        try:
            page_path = container.settings.frontend_dir / "pages" / "course_create.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/courses/edit/{course_id}")
    async def edit_course_page(course_id: int) -> FileResponse:
        _ = course_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "course_edit.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/courses/{course_id}/stats")
    async def course_stats_page(course_id: int) -> FileResponse:
        _ = course_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "course_stats.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/courses/{course_id}")
    async def course_detail_page(course_id: int) -> FileResponse:
        _ = course_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "course_detail.html"
            return _html_file_response(page_path)
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/edit/tablature/{tablature_id}")
    async def edit_tablature_detail_page(tablature_id: int) -> FileResponse:
        _ = tablature_id
        try:
            page_path = container.settings.frontend_dir / "pages" / "edit_tablature_detail.html"
            return _html_file_response(page_path)
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

    @router.get("/api/courses")
    async def list_public_courses(
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            items = await container.list_public_courses.execute(query=q, limit=limit, offset=offset)
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "author": item.author,
                        "visibility": item.visibility,
                        "tags": item.tags,
                        "cover_image_path": item.cover_image_path,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/community/courses/{course_id}/lessons")
    async def list_public_course_lessons(course_id: int) -> dict:
        try:
            items = await container.list_public_course_lessons.execute(course_id=course_id)
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "course_id": item.course_id,
                        "title": item.title,
                        "content": item.content,
                        "position": item.position,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/courses")
    async def create_course(
        payload: CreateCourseRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            course = await container.create_course.execute(
                token=token,
                title=payload.title,
                description=payload.description,
                visibility=payload.visibility,
                tags=payload.tags,
                cover_image_path=payload.cover_image_path,
            )
            return {
                "course": {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "author": course.author,
                    "visibility": course.visibility,
                    "tags": course.tags,
                    "cover_image_path": course.cover_image_path,
                    "created_at": course.created_at,
                    "updated_at": course.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/courses/cover")
    async def upload_course_cover(
        file: UploadFile = File(...),
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            user = await container.get_current_user.execute(token=token)
            if str(user.get("role") or "").strip().lower() != "author":
                raise HTTPException(status_code=403, detail="Only author can upload course cover")

            content_type = str(file.content_type or "").lower()
            if not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Unsupported file type. Image required")

            data = await file.read()
            if not data:
                raise HTTPException(status_code=400, detail="Uploaded image is empty")
            if len(data) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image is too large (max 5MB)")

            suffix = Path(file.filename or "").suffix.lower()
            allowed_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
            if suffix not in allowed_suffixes:
                content_type_to_suffix = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/webp": ".webp",
                    "image/gif": ".gif",
                    "image/svg+xml": ".svg",
                }
                suffix = content_type_to_suffix.get(content_type, "")
            if suffix not in allowed_suffixes:
                raise HTTPException(status_code=400, detail="Unsupported image format")

            if container.object_storage is not None:
                object_key = f"covers/{uuid4().hex}{suffix}"
                await container.object_storage.upload_bytes(
                    object_key=object_key,
                    data=data,
                    content_type=content_type or "application/octet-stream",
                )
                return {"cover_image_path": f"/api/media/{object_key}"}

            assets_dir = Path(container.frontend_assets_dir)
            cover_dir = assets_dir / "images" / "courses"
            cover_dir.mkdir(parents=True, exist_ok=True)

            file_name = f"{uuid4().hex}{suffix}"
            save_path = cover_dir / file_name
            save_path.write_bytes(data)
            return {"cover_image_path": f"/assets/images/courses/{file_name}"}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/media/{object_key:path}")
    async def get_media_object(object_key: str) -> Response:
        try:
            if container.object_storage is None:
                raise HTTPException(status_code=404, detail="Media storage is not configured")

            payload, media_type = await container.object_storage.get_bytes(object_key=object_key)
            return Response(
                content=payload,
                media_type=media_type or "application/octet-stream",
                headers={"Cache-Control": "public, max-age=604800"},
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Media object not found")
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

    @router.get("/api/personal/courses")
    async def list_personal_courses(
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_personal_courses.execute(
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
                        "title": item.title,
                        "description": item.description,
                        "author": item.author,
                        "visibility": item.visibility,
                        "tags": item.tags,
                        "cover_image_path": item.cover_image_path,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/personal/courses/{course_id}")
    async def patch_personal_course(
        course_id: int,
        payload: UpdatePersonalCourseRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            course = await container.update_personal_course.execute(
                token=token,
                course_id=course_id,
                title=payload.title,
                description=payload.description,
                visibility=payload.visibility,
                tags=payload.tags,
                cover_image_path=payload.cover_image_path,
            )
            return {
                "course": {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "author": course.author,
                    "visibility": course.visibility,
                    "tags": course.tags,
                    "cover_image_path": course.cover_image_path,
                    "created_at": course.created_at,
                    "updated_at": course.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/personal/courses/{course_id}")
    async def delete_personal_course(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_personal_course.execute(
                token=token,
                course_id=course_id,
            )
            return {"deleted": bool(deleted)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/personal/courses/{course_id}/lessons")
    async def list_personal_course_lessons(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_personal_course_lessons.execute(
                token=token,
                course_id=course_id,
            )
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "course_id": item.course_id,
                        "title": item.title,
                        "content": item.content,
                        "position": item.position,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/personal/courses/{course_id}/lessons/progress")
    async def list_personal_course_lesson_progress(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_personal_course_lesson_progress.execute(
                token=token,
                course_id=course_id,
            )
            return {
                "count": len(items),
                "items": [
                    {
                        "lesson_id": item.lesson_id,
                        "is_completed": item.is_completed,
                        "completed_at": item.completed_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/personal/courses/{course_id}/visit")
    async def track_personal_course_visit(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            visit = await container.track_personal_course_visit.execute(
                token=token,
                course_id=course_id,
            )
            return {
                "visit": {
                    "user_id": visit.user_id,
                    "course_id": visit.course_id,
                    "is_first_visit": visit.is_first_visit,
                    "first_visit_at": visit.first_visit_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/personal/courses/{course_id}/stats")
    async def get_personal_course_statistics(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            stats = await container.get_personal_course_statistics.execute(
                token=token,
                course_id=course_id,
            )
            return {
                "stats": {
                    "course_id": stats.course_id,
                    "course_title": stats.course_title,
                    "visitors": [
                        {
                            "user_id": item.user_id,
                            "user_name": item.user_name,
                            "first_visit_at": item.first_visit_at,
                        }
                        for item in stats.visitors
                    ],
                    "lesson_completions": [
                        {
                            "user_id": item.user_id,
                            "user_name": item.user_name,
                            "lesson_id": item.lesson_id,
                            "lesson_title": item.lesson_title,
                            "completed_at": item.completed_at,
                        }
                        for item in stats.lesson_completions
                    ],
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/personal/courses/{course_id}/lessons")
    async def create_personal_course_lesson(
        course_id: int,
        payload: CreateCourseLessonRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            lesson = await container.create_personal_course_lesson.execute(
                token=token,
                course_id=course_id,
                title=payload.title,
                content=payload.content,
                position=payload.position,
            )
            return {
                "lesson": {
                    "id": lesson.id,
                    "course_id": lesson.course_id,
                    "title": lesson.title,
                    "content": lesson.content,
                    "position": lesson.position,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/personal/courses/{course_id}/lessons/{lesson_id}/progress")
    async def patch_personal_course_lesson_progress(
        course_id: int,
        lesson_id: int,
        payload: SetLessonProgressRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            progress = await container.set_personal_course_lesson_progress.execute(
                token=token,
                course_id=course_id,
                lesson_id=lesson_id,
                completed=payload.completed,
            )
            return {
                "progress": {
                    "lesson_id": progress.lesson_id,
                    "is_completed": progress.is_completed,
                    "completed_at": progress.completed_at,
                    "updated_at": progress.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/personal/courses/{course_id}/lessons/{lesson_id}")
    async def patch_personal_course_lesson(
        course_id: int,
        lesson_id: int,
        payload: UpdateCourseLessonRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            lesson = await container.update_personal_course_lesson.execute(
                token=token,
                course_id=course_id,
                lesson_id=lesson_id,
                title=payload.title,
                content=payload.content,
                position=payload.position,
            )
            return {
                "lesson": {
                    "id": lesson.id,
                    "course_id": lesson.course_id,
                    "title": lesson.title,
                    "content": lesson.content,
                    "position": lesson.position,
                    "created_at": lesson.created_at,
                    "updated_at": lesson.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/personal/courses/{course_id}/lessons/{lesson_id}")
    async def delete_personal_course_lesson(
        course_id: int,
        lesson_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_personal_course_lesson.execute(
                token=token,
                course_id=course_id,
                lesson_id=lesson_id,
            )
            return {"deleted": bool(deleted)}
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

    @router.get("/api/personal/author-role-request")
    async def get_personal_author_role_request(authorization: Optional[str] = Header(default=None)) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            request_item = await container.get_personal_author_role_request.execute(token=token)
            if request_item is None:
                return {"request": None}
            return {
                "request": {
                    "id": request_item.id,
                    "user_id": request_item.user_id,
                    "message": request_item.message,
                    "status": request_item.status,
                    "admin_message": request_item.admin_message,
                    "created_at": request_item.created_at,
                    "updated_at": request_item.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.post("/api/personal/author-role-request")
    async def create_personal_author_role_request(
        payload: CreateAuthorRoleRequestPayload,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            request_item = await container.create_personal_author_role_request.execute(
                token=token,
                message=payload.message,
            )
            return {
                "request": {
                    "id": request_item.id,
                    "user_id": request_item.user_id,
                    "message": request_item.message,
                    "status": request_item.status,
                    "admin_message": request_item.admin_message,
                    "created_at": request_item.created_at,
                    "updated_at": request_item.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/tablatures")
    async def list_admin_tablatures(
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_tablatures.execute(
                token=token,
                query=q,
                limit=limit,
                offset=offset,
            )
            return {"count": len(items), "items": items}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/courses")
    async def list_admin_courses(
        authorization: Optional[str] = Header(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_courses.execute(
                token=token,
                query=q,
                limit=limit,
                offset=offset,
            )
            return {"count": len(items), "items": items}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/tablatures/{tablature_id}")
    async def get_admin_tablature_by_id(
        tablature_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            tablature = await container.get_admin_tablature_by_id.execute(
                token=token,
                tablature_id=tablature_id,
            )
            return {"tablature": tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/admin/tablatures/{tablature_id}/visibility")
    async def patch_admin_tablature_visibility(
        tablature_id: int,
        payload: UpdateAdminVisibilityRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            tablature = await container.update_admin_tablature_visibility.execute(
                token=token,
                tablature_id=tablature_id,
                visibility=payload.visibility,
            )
            return {"tablature": tablature}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/admin/tablatures/{tablature_id}")
    async def delete_admin_tablature(
        tablature_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_admin_tablature.execute(
                token=token,
                tablature_id=tablature_id,
            )
            return {"deleted": bool(deleted)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/tablatures/{tablature_id}/comments")
    async def list_admin_tablature_comments(
        tablature_id: int,
        authorization: Optional[str] = Header(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_tablature_comments.execute(
                token=token,
                tablature_id=tablature_id,
                limit=limit,
                offset=offset,
            )
            return {"count": len(items), "items": items}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/admin/tablatures/{tablature_id}/comments/{comment_id}")
    async def delete_admin_tablature_comment(
        tablature_id: int,
        comment_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_admin_tablature_comment.execute(
                token=token,
                tablature_id=tablature_id,
                comment_id=comment_id,
            )
            return {"deleted": bool(deleted)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/courses/{course_id}")
    async def get_admin_course_by_id(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            course = await container.get_admin_course_by_id.execute(
                token=token,
                course_id=course_id,
            )
            return {"course": course}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/admin/courses/{course_id}/visibility")
    async def patch_admin_course_visibility(
        course_id: int,
        payload: UpdateAdminVisibilityRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            course = await container.update_admin_course_visibility.execute(
                token=token,
                course_id=course_id,
                visibility=payload.visibility,
            )
            return {"course": course}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/admin/courses/{course_id}")
    async def delete_admin_course(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_admin_course.execute(
                token=token,
                course_id=course_id,
            )
            return {"deleted": bool(deleted)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/courses/{course_id}/lessons")
    async def list_admin_course_lessons(
        course_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_course_lessons.execute(
                token=token,
                course_id=course_id,
            )
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "course_id": item.course_id,
                        "title": item.title,
                        "content": item.content,
                        "position": item.position,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/users")
    async def list_admin_users(
        authorization: Optional[str] = Header(default=None),
        role: Optional[str] = Query(default="all"),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_users.execute(
                token=token,
                role=role,
                query=q,
                limit=limit,
                offset=offset,
            )
            return {"count": len(items), "items": items}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/admin/users/{user_id}")
    async def patch_admin_user_account(
        user_id: int,
        payload: UpdateAdminUserAccountRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            user = await container.update_admin_user_account.execute(
                token=token,
                user_id=user_id,
                email=payload.email,
                nickname=payload.nickname,
                role=payload.role,
            )
            return {"user": user}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.delete("/api/admin/users/{user_id}")
    async def delete_admin_user(
        user_id: int,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            deleted = await container.delete_admin_user.execute(
                token=token,
                user_id=user_id,
            )
            return {"deleted": bool(deleted)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/api/admin/author-role-requests")
    async def list_admin_author_role_requests(
        authorization: Optional[str] = Header(default=None),
        status: Optional[str] = Query(default="pending"),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            items = await container.list_admin_author_role_requests.execute(
                token=token,
                status=status,
                limit=limit,
                offset=offset,
            )
            return {
                "count": len(items),
                "items": [
                    {
                        "id": item.id,
                        "user_id": item.user_id,
                        "user_email": item.user_email,
                        "user_nickname": item.user_nickname,
                        "message": item.message,
                        "status": item.status,
                        "admin_message": item.admin_message,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                    }
                    for item in items
                ],
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.patch("/api/admin/author-role-requests/{request_id}")
    async def patch_admin_author_role_request(
        request_id: int,
        payload: UpdateAdminAuthorRoleRequestPayload,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            token = _extract_bearer_token(authorization)
            item = await container.update_admin_author_role_request.execute(
                token=token,
                request_id=request_id,
                status=payload.status,
                admin_message=payload.admin_message,
            )
            return {
                "request": {
                    "id": item.id,
                    "user_id": item.user_id,
                    "user_email": item.user_email,
                    "user_nickname": item.user_nickname,
                    "message": item.message,
                    "status": item.status,
                    "admin_message": item.admin_message,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise to_http_exception(exc) from exc

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return router
