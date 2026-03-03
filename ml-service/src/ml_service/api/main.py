from __future__ import annotations

import asyncio

from fastapi import FastAPI

from ml_service.api.routes_jobs import router as jobs_router
from ml_service.bootstrap import get_container

app = FastAPI(title="ml-service", version="0.1.0")
app.include_router(jobs_router)


@app.on_event("startup")
async def on_startup() -> None:
    container = get_container()
    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(
        container.job_service.run_worker_loop(
            stop_event=stop_event,
            poll_timeout_sec=container.settings.worker_poll_timeout_sec,
        )
    )
    app.state.stop_event = stop_event
    app.state.worker_task = worker_task


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_event: asyncio.Event = app.state.stop_event
    worker_task: asyncio.Task = app.state.worker_task

    stop_event.set()
    await worker_task


@app.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict:
    return {"status": "ok"}

