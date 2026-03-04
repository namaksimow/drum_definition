from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.bootstrap import get_container
from app.domain.errors import DatabaseUnavailableError

router = APIRouter()


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
