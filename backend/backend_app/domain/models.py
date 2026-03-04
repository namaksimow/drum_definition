from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class UploadedJob:
    id: str
    status: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class PdfArtifact:
    file_path: Path
    download_filename: str

