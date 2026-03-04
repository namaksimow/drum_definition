from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FrontendPort(Protocol):
    def index_path(self) -> Path:
        ...

    def assets_dir(self) -> Path:
        ...

