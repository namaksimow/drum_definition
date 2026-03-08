from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UploadedJob:
    id: str
    status: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class PdfArtifact:
    content: bytes
    download_filename: str


@dataclass(frozen=True)
class TablatureArtifact:
    job_id: str
    tablature: dict[str, Any]


@dataclass(frozen=True)
class JobInfoArtifact:
    id: str
    status: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class CommunityTablatureItem:
    id: int
    task_id: int
    track_file_name: str
    author: str
    result_path: str | None
    created_at: str
    comments_count: int = 0
    reactions_like_count: int = 0
    reactions_fire_count: int = 0
    reactions_wow_count: int = 0


@dataclass(frozen=True)
class JsonArtifact:
    content: bytes
    download_filename: str
