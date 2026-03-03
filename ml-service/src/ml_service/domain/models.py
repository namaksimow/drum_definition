from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

JobStatus = Literal["queued", "processing", "done", "failed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    id: str
    filename: str
    input_key: str
    status: JobStatus
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    result_manifest: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "input_key": self.input_key,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result_manifest": self.result_manifest,
            "error": self.error,
        }

