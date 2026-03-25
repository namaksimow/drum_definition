from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from rabbitmq_app.broker import RabbitBroker
from rabbitmq_app.config import Settings, get_settings


class PublishJobPayload(BaseModel):
    job_id: str = Field(min_length=1, max_length=128)


@lru_cache(maxsize=1)
def _build_broker() -> RabbitBroker:
    settings: Settings = get_settings()
    return RabbitBroker(
        amqp_url=settings.rabbitmq_url,
        queue_name=settings.rabbitmq_queue_name,
        prefetch_count=settings.rabbitmq_prefetch_count,
        connect_timeout_sec=settings.rabbitmq_connect_timeout_sec,
    )


app = FastAPI(title="rabbitmq-service", version="0.1.0")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    broker = _build_broker()
    await broker.close()


@app.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict:
    broker = _build_broker()
    try:
        await broker.ensure_ready()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/jobs")
async def publish_job(payload: PublishJobPayload) -> dict:
    broker = _build_broker()
    try:
        await broker.publish_job(payload.job_id)
        return {"job_id": payload.job_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/v1/jobs/consume")
async def consume_job(timeout_sec: float = Query(default=1.0, ge=0.0, le=60.0)) -> dict:
    broker = _build_broker()
    try:
        job_id = await broker.consume_job(timeout_sec=timeout_sec)
        return {"job_id": job_id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

