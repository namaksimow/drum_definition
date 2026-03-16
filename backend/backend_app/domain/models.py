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
class CourseItem:
    id: int
    title: str
    description: str | None
    author: str
    visibility: str
    tags: list[str]
    cover_image_path: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CourseLessonItem:
    id: int
    course_id: int
    title: str
    content: str
    position: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CourseLessonProgressItem:
    lesson_id: int
    is_completed: bool
    completed_at: str | None
    updated_at: str | None


@dataclass(frozen=True)
class CourseVisitMarkerItem:
    user_id: int
    course_id: int
    is_first_visit: bool
    first_visit_at: str | None


@dataclass(frozen=True)
class CourseVisitorStatItem:
    user_id: int
    user_name: str
    first_visit_at: str


@dataclass(frozen=True)
class CourseLessonCompletionStatItem:
    user_id: int
    user_name: str
    lesson_id: int
    lesson_title: str
    completed_at: str


@dataclass(frozen=True)
class CourseStatisticsItem:
    course_id: int
    course_title: str
    visitors: list[CourseVisitorStatItem]
    lesson_completions: list[CourseLessonCompletionStatItem]


@dataclass(frozen=True)
class AuthorRoleRequestItem:
    id: int
    user_id: int
    message: str
    status: str
    admin_message: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AdminAuthorRoleRequestItem:
    id: int
    user_id: int
    user_email: str
    user_nickname: str
    message: str
    status: str
    admin_message: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class JsonArtifact:
    content: bytes
    download_filename: str
