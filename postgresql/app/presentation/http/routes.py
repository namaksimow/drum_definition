from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.bootstrap import get_container
from app.domain.errors import DatabaseUnavailableError

router = APIRouter()


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


class UpdateAuthorRoleRequestStatusPayload(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    admin_message: Optional[str] = Field(default=None, max_length=5000)


class UpdateMyTablatureRequest(BaseModel):
    track_file_name: Optional[str] = Field(default=None, max_length=255)
    visibility: Optional[str] = Field(default=None, max_length=64)
    json_format: Optional[dict] = None


class CreateTablatureCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SetTablatureReactionRequest(BaseModel):
    reaction_type: str = Field(min_length=1, max_length=32)


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    visibility: Optional[str] = Field(default="public", max_length=64)
    tags: List[str] = Field(default_factory=list)
    cover_image_path: Optional[str] = Field(default=None, max_length=1000)


class UpdateMyCourseRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    visibility: Optional[str] = Field(default=None, max_length=64)
    tags: Optional[List[str]] = None
    cover_image_path: Optional[str] = Field(default=None, max_length=1000)


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


class UpdateVisibilityRequest(BaseModel):
    visibility: str = Field(min_length=1, max_length=64)


class UpdateAdminUserAccountRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=320)
    nickname: Optional[str] = Field(default=None, max_length=64)
    role: Optional[str] = Field(default=None, max_length=32)


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


@router.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready() -> dict:
    container = get_container()
    try:
        await container.check_db_health.execute()
        return {"status": "ok"}
    except DatabaseUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/db/tables")
async def db_tables() -> dict:
    container = get_container()
    return {"tables": await container.list_tables.execute()}


@router.get("/community/tablatures")
async def list_public_tablatures(
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    container = get_container()
    items = await container.list_public_tablatures.execute(query=q, limit=limit, offset=offset)
    return {"count": len(items), "items": items}


@router.get("/community/courses")
async def list_public_courses(
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    container = get_container()
    items = await container.list_public_courses.execute(query=q, limit=limit, offset=offset)
    return {"count": len(items), "items": items}


@router.get("/community/courses/{course_id}/lessons")
async def list_public_course_lessons(course_id: int) -> dict:
    container = get_container()
    items = await container.list_public_course_lessons.execute(course_id=course_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Public course not found")
    return {"count": len(items), "items": items}


@router.post("/me/courses")
async def create_course(
    payload: CreateCourseRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "author":
        raise HTTPException(status_code=403, detail="Only author can create courses")

    try:
        course = await container.create_course.execute(
            user_id=int(user["id"]),
            title=payload.title,
            description=payload.description,
            visibility=payload.visibility,
            tags=payload.tags,
            cover_image_path=payload.cover_image_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"course": course}


@router.get("/me/courses")
async def list_my_courses(
    authorization: Optional[str] = Header(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    items = await container.list_user_courses.execute(
        user_id=int(user["id"]),
        query=q,
        limit=limit,
        offset=offset,
    )
    return {"count": len(items), "items": items}


@router.patch("/me/courses/{course_id}")
async def patch_my_course(
    course_id: int,
    payload: UpdateMyCourseRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        updated = await container.update_user_course.execute(
            user_id=int(user["id"]),
            course_id=course_id,
            title=payload.title,
            description=payload.description,
            visibility=payload.visibility,
            tags=payload.tags,
            cover_image_path=payload.cover_image_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"course": updated}


@router.delete("/me/courses/{course_id}")
async def delete_my_course(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    deleted = await container.delete_user_course.execute(
        user_id=int(user["id"]),
        course_id=course_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"deleted": True}


@router.get("/me/courses/{course_id}/lessons")
async def list_my_course_lessons(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    items = await container.list_user_course_lessons.execute(
        user_id=int(user["id"]),
        course_id=course_id,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"count": len(items), "items": items}


@router.get("/me/courses/{course_id}/lessons/progress")
async def list_my_course_lesson_progress(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    items = await container.list_user_course_lesson_progress.execute(
        user_id=int(user["id"]),
        course_id=course_id,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"count": len(items), "items": items}


@router.post("/me/courses/{course_id}/visit")
async def track_my_course_visit(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    visit = await container.track_user_course_visit.execute(
        user_id=int(user["id"]),
        course_id=course_id,
    )
    if visit is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"visit": visit}


@router.get("/me/courses/{course_id}/stats")
async def get_my_course_statistics(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "author":
        raise HTTPException(status_code=403, detail="Only author can view course statistics")

    stats = await container.get_author_course_statistics.execute(
        author_user_id=int(user["id"]),
        course_id=course_id,
    )
    if stats is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"stats": stats}


@router.post("/me/courses/{course_id}/lessons")
async def create_my_course_lesson(
    course_id: int,
    payload: CreateCourseLessonRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        lesson = await container.create_user_course_lesson.execute(
            user_id=int(user["id"]),
            course_id=course_id,
            title=payload.title,
            content=payload.content,
            position=payload.position,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if lesson is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"lesson": lesson}


@router.patch("/me/courses/{course_id}/lessons/{lesson_id}/progress")
async def patch_my_course_lesson_progress(
    course_id: int,
    lesson_id: int,
    payload: SetLessonProgressRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    progress = await container.set_user_course_lesson_progress.execute(
        user_id=int(user["id"]),
        course_id=course_id,
        lesson_id=lesson_id,
        completed=payload.completed,
    )
    if progress is None:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    return {"progress": progress}


@router.patch("/me/courses/{course_id}/lessons/{lesson_id}")
async def patch_my_course_lesson(
    course_id: int,
    lesson_id: int,
    payload: UpdateCourseLessonRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        lesson = await container.update_user_course_lesson.execute(
            user_id=int(user["id"]),
            course_id=course_id,
            lesson_id=lesson_id,
            title=payload.title,
            content=payload.content,
            position=payload.position,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if lesson is None:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    return {"lesson": lesson}


@router.delete("/me/courses/{course_id}/lessons/{lesson_id}")
async def delete_my_course_lesson(
    course_id: int,
    lesson_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    deleted = await container.delete_user_course_lesson.execute(
        user_id=int(user["id"]),
        course_id=course_id,
        lesson_id=lesson_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    return {"deleted": True}


@router.get("/community/tablatures/{tablature_id}")
async def get_public_tablature(tablature_id: int) -> dict:
    container = get_container()
    item = await container.get_public_tablature.execute(tablature_id=tablature_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Public tablature not found")
    return {"tablature": item}


@router.get("/community/tablatures/{tablature_id}/comments")
async def list_public_tablature_comments(
    tablature_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    container = get_container()
    items = await container.list_public_tablature_comments.execute(
        tablature_id=tablature_id,
        limit=limit,
        offset=offset,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Public tablature not found")
    return {"count": len(items), "items": items}


@router.post("/community/tablatures/{tablature_id}/comments")
async def create_public_tablature_comment(
    tablature_id: int,
    payload: CreateTablatureCommentRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        comment = await container.add_public_tablature_comment.execute(
            tablature_id=tablature_id,
            user_id=int(user["id"]),
            content=payload.content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if comment is None:
        raise HTTPException(status_code=404, detail="Public tablature not found")
    return {"comment": comment}


@router.get("/community/tablatures/{tablature_id}/reactions")
async def get_public_tablature_reactions(
    tablature_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    container = get_container()
    user_id: int | None = None
    if authorization is not None:
        token = _extract_bearer_token(authorization)
        try:
            user = await container.get_current_user.execute(token=token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        user_id = int(user["id"])

    reactions = await container.get_public_tablature_reactions.execute(
        tablature_id=tablature_id,
        user_id=user_id,
    )
    if reactions is None:
        raise HTTPException(status_code=404, detail="Public tablature not found")
    return {"reactions": reactions}


@router.post("/community/tablatures/{tablature_id}/reactions")
async def set_public_tablature_reaction(
    tablature_id: int,
    payload: SetTablatureReactionRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        reactions = await container.set_public_tablature_reaction.execute(
            tablature_id=tablature_id,
            user_id=int(user["id"]),
            reaction_type=payload.reaction_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if reactions is None:
        raise HTTPException(status_code=404, detail="Public tablature not found")
    return {"reactions": reactions}


@router.post("/auth/register")
async def register_user(payload: RegisterRequest) -> dict:
    container = get_container()
    try:
        user = await container.register_user.execute(
            email=str(payload.email),
            password=payload.password,
            nickname=payload.nickname,
        )
        return {"user": user}
    except ValueError as exc:
        message = str(exc)
        status_code = 409 if "already exists" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post("/auth/login")
async def login_user(payload: LoginRequest) -> dict:
    container = get_container()
    try:
        return await container.login_user.execute(
            email=str(payload.email),
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/auth/me")
async def get_auth_me(authorization: Optional[str] = Header(default=None)) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"user": user}


@router.patch("/auth/me")
async def patch_auth_me(payload: UpdateMeRequest, authorization: Optional[str] = Header(default=None)) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.update_current_user_nickname.execute(
            token=token,
            nickname=payload.nickname,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 401 if "token" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from exc
    return {"user": user}


@router.get("/me/author-role-request")
async def get_my_author_role_request(
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    request_item = await container.get_latest_author_role_request.execute(
        user_id=int(user["id"]),
    )
    return {"request": request_item}


@router.post("/me/author-role-request")
async def create_my_author_role_request(
    payload: CreateAuthorRoleRequestPayload,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        request_item = await container.create_author_role_request.execute(
            user_id=int(user["id"]),
            message=payload.message,
        )
    except ValueError as exc:
        message = str(exc)
        if "already has author role" in message.lower():
            raise HTTPException(status_code=409, detail=message) from exc
        if "already exists" in message.lower():
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc
    return {"request": request_item}


@router.get("/admin/tablatures")
async def list_admin_tablatures(
    authorization: Optional[str] = Header(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view tablatures")

    items = await container.list_admin_tablatures.execute(
        query=q,
        limit=limit,
        offset=offset,
    )
    return {"count": len(items), "items": items}


@router.get("/admin/tablatures/{tablature_id}")
async def get_admin_tablature(
    tablature_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view tablatures")

    item = await container.get_admin_tablature.execute(tablature_id=tablature_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"tablature": item}


@router.patch("/admin/tablatures/{tablature_id}/visibility")
async def patch_admin_tablature_visibility(
    tablature_id: int,
    payload: UpdateVisibilityRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update tablatures")

    try:
        item = await container.update_admin_tablature_visibility.execute(
            tablature_id=tablature_id,
            visibility=payload.visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"tablature": item}


@router.delete("/admin/tablatures/{tablature_id}")
async def delete_admin_tablature(
    tablature_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete tablatures")

    deleted = await container.delete_admin_tablature.execute(tablature_id=tablature_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"deleted": True}


@router.get("/admin/tablatures/{tablature_id}/comments")
async def list_admin_tablature_comments(
    tablature_id: int,
    authorization: Optional[str] = Header(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view tablature comments")

    items = await container.list_admin_tablature_comments.execute(
        tablature_id=tablature_id,
        limit=limit,
        offset=offset,
    )
    if items is None:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"count": len(items), "items": items}


@router.delete("/admin/tablatures/{tablature_id}/comments/{comment_id}")
async def delete_admin_tablature_comment(
    tablature_id: int,
    comment_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete tablature comments")

    deleted = await container.delete_admin_tablature_comment.execute(
        tablature_id=tablature_id,
        comment_id=comment_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"deleted": True}


@router.get("/admin/courses")
async def list_admin_courses(
    authorization: Optional[str] = Header(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view courses")

    items = await container.list_admin_courses.execute(
        query=q,
        limit=limit,
        offset=offset,
    )
    return {"count": len(items), "items": items}


@router.get("/admin/courses/{course_id}")
async def get_admin_course(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view courses")

    item = await container.get_admin_course.execute(course_id=course_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"course": item}


@router.patch("/admin/courses/{course_id}/visibility")
async def patch_admin_course_visibility(
    course_id: int,
    payload: UpdateVisibilityRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update courses")

    try:
        item = await container.update_admin_course_visibility.execute(
            course_id=course_id,
            visibility=payload.visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"course": item}


@router.delete("/admin/courses/{course_id}")
async def delete_admin_course(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete courses")

    deleted = await container.delete_admin_course.execute(course_id=course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"deleted": True}


@router.get("/admin/courses/{course_id}/lessons")
async def list_admin_course_lessons(
    course_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view course lessons")

    items = await container.list_admin_course_lessons.execute(course_id=course_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"count": len(items), "items": items}


@router.get("/admin/users")
async def list_admin_users(
    authorization: Optional[str] = Header(default=None),
    role: Optional[str] = Query(default="all"),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view users")

    try:
        items = await container.list_admin_users.execute(
            role=role,
            query=q,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"count": len(items), "items": items}


@router.patch("/admin/users/{user_id}")
async def patch_admin_user_account(
    user_id: int,
    payload: UpdateAdminUserAccountRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update users")

    try:
        updated = await container.update_admin_user_account.execute(
            user_id=user_id,
            email=payload.email,
            nickname=payload.nickname,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": updated}


@router.delete("/admin/users/{user_id}")
async def delete_admin_user(
    user_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")

    deleted = await container.delete_admin_user.execute(user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}


@router.get("/admin/author-role-requests")
async def list_admin_author_role_requests(
    authorization: Optional[str] = Header(default=None),
    status: Optional[str] = Query(default="pending"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view author role requests")

    items = await container.list_author_role_requests.execute(
        status=status,
        limit=limit,
        offset=offset,
    )
    return {"count": len(items), "items": items}


@router.patch("/admin/author-role-requests/{request_id}")
async def patch_admin_author_role_request(
    request_id: int,
    payload: UpdateAuthorRoleRequestStatusPayload,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if str(user.get("role") or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update author role requests")

    try:
        item = await container.update_author_role_request_status.execute(
            request_id=request_id,
            status=payload.status,
            admin_message=payload.admin_message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Author role request not found")
    return {"request": item}


@router.get("/me/tablatures")
async def list_personal_tablatures(
    authorization: Optional[str] = Header(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    items = await container.list_user_tablatures.execute(
        user_id=int(user["id"]),
        query=q,
        limit=limit,
        offset=offset,
    )
    return {"count": len(items), "items": items}


@router.get("/me/tablatures/{tablature_id}")
async def get_personal_tablature(
    tablature_id: int,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    tablature = await container.get_user_tablature.execute(
        user_id=int(user["id"]),
        tablature_id=tablature_id,
    )
    if tablature is None:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"tablature": tablature}


@router.patch("/me/tablatures/{tablature_id}")
async def patch_personal_tablature(
    tablature_id: int,
    payload: UpdateMyTablatureRequest,
    authorization: Optional[str] = Header(default=None),
) -> dict:
    token = _extract_bearer_token(authorization)
    container = get_container()
    try:
        user = await container.get_current_user.execute(token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        updated = await container.update_user_tablature.execute(
            user_id=int(user["id"]),
            tablature_id=tablature_id,
            track_file_name=payload.track_file_name,
            visibility=payload.visibility,
            json_format=payload.json_format,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 409 if "already exists" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Tablature not found")
    return {"tablature": updated}
