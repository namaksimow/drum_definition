from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend_app.bootstrap import get_container
from backend_app.presentation.http.routes import build_router


def create_app() -> FastAPI:
    container = get_container()
    app = FastAPI(title="simple-backend", version="0.1.0")
    app.mount("/assets", StaticFiles(directory=container.frontend_assets_dir), name="assets")
    app.include_router(build_router(container))
    return app

app = create_app()
