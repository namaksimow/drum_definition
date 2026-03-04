from __future__ import annotations

from pathlib import Path

from backend_app.application.ports.frontend_port import FrontendPort


class FrontendFilesystemAdapter(FrontendPort):
    def __init__(self, frontend_dir: Path) -> None:
        self._frontend_dir = frontend_dir

    def index_path(self) -> Path:
        return self._frontend_dir / "pages" / "index.html"

    def assets_dir(self) -> Path:
        return self._frontend_dir / "assets"

