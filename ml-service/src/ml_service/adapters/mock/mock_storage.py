from __future__ import annotations

from pathlib import Path

from ml_service.ports.file_storage import FileStorage


def _sanitize_filename(filename: str) -> str:
    return Path(filename).name.replace(" ", "_")


class MockFileStorage(FileStorage):
    def __init__(self, base_dir: str | Path = "data") -> None:
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.results_dir = self.base_dir / "results"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, job_id: str, filename: str, data: bytes) -> str:
        safe_name = _sanitize_filename(filename)
        key = f"{job_id}_{safe_name}"
        path = self.uploads_dir / key
        path.write_bytes(data)
        return key

    async def resolve_input_path(self, input_key: str) -> Path:
        path = self.uploads_dir / input_key
        if not path.exists():
            raise FileNotFoundError(f"Upload not found for key: {input_key}")
        return path

    async def prepare_results_dir(self, job_id: str) -> Path:
        path = self.results_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

