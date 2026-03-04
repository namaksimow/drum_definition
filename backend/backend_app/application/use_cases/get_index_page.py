from __future__ import annotations

from pathlib import Path

from backend_app.application.ports.frontend_port import FrontendPort
from backend_app.domain.errors import NotFoundError


class GetIndexPageUseCase:
    def __init__(self, frontend: FrontendPort) -> None:
        self.frontend = frontend

    def execute(self) -> Path:
        index = self.frontend.index_path()
        if not index.exists():
            raise NotFoundError("Frontend page not found")
        return index

