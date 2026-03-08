from __future__ import annotations

from typing import Optional

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


class UpdateMyTablatureRequest(BaseModel):
    track_file_name: Optional[str] = Field(default=None, max_length=255)
    visibility: Optional[str] = Field(default=None, max_length=64)
    json_format: Optional[dict] = None


class CreateTablatureCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SetTablatureReactionRequest(BaseModel):
    reaction_type: str = Field(min_length=1, max_length=32)


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
