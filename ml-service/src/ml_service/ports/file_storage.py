from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    async def save_upload(self, job_id: str, filename: str, data: bytes) -> str:
        ...

    async def resolve_input_path(self, input_key: str) -> Path:
        ...

    async def prepare_results_dir(self, job_id: str) -> Path:
        ...

