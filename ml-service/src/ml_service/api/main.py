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
    app.state.stop_event = None
    app.state.worker_task = None

    if container.settings.run_worker_in_api:
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
    stop_event: asyncio.Event | None = app.state.stop_event
    worker_task: asyncio.Task | None = app.state.worker_task

    if stop_event is not None and worker_task is not None:
        stop_event.set()
        await worker_task

    container = get_container()
    close_queue = getattr(container.job_queue, "close", None)
    if callable(close_queue):
        await close_queue()


@app.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict:
    return {"status": "ok"}
