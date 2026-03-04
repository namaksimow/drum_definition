from __future__ import annotations

from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class Visibility(Base):
    __tablename__ = "visibilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class Status(Base):
    __tablename__ = "status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("idx_users_role_id", "role_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", onupdate="CASCADE"),
        nullable=False,
    )


class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        CheckConstraint("duration >= 0", name="ck_tracks_duration_non_negative"),
        Index("idx_tracks_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)


class Course(Base):
    __tablename__ = "course"
    __table_args__ = (
        Index("idx_course_user_id", "user_id"),
        Index("idx_course_visibility_id", "visibility_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    visibility_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("visibilities.id", onupdate="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_image_path: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Task(Base):
    __tablename__ = "task"
    __table_args__ = (
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at",
            name="ck_task_finished_after_started",
        ),
        Index("idx_task_track_id", "track_id"),
        Index("idx_task_status_id", "status_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tracks.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("status.id", onupdate="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))


class Tablature(Base):
    __tablename__ = "tablatures"
    __table_args__ = (
        Index("idx_tablatures_task_id", "task_id"),
        Index("idx_tablatures_visibility_id", "visibility_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    visibility_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("visibilities.id", onupdate="CASCADE"),
        nullable=False,
    )
    json_format: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_path: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseReaction(Base):
    __tablename__ = "course_reactions"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", "reaction_type", name="uq_course_reactions_triplet"),
        Index("idx_course_reactions_course_id", "course_id"),
        Index("idx_course_reactions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    reaction_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CourseComment(Base):
    __tablename__ = "course_comments"
    __table_args__ = (
        Index("idx_course_comments_course_id", "course_id"),
        Index("idx_course_comments_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TablatureReaction(Base):
    __tablename__ = "tablature_reactions"
    __table_args__ = (
        UniqueConstraint("tablature_id", "user_id", "reaction_type", name="uq_tablature_reactions_triplet"),
        Index("idx_tabl_reactions_tabl_id", "tablature_id"),
        Index("idx_tabl_reactions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tablature_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tablatures.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    reaction_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TablatureComment(Base):
    __tablename__ = "tablature_comments"
    __table_args__ = (
        Index("idx_tabl_comments_tabl_id", "tablature_id"),
        Index("idx_tabl_comments_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    tablature_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tablatures.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Statistic(Base):
    __tablename__ = "statistics"
    __table_args__ = (
        Index("idx_statistics_user_id", "user_id"),
        Index("idx_statistics_course_id", "course_id"),
        Index("idx_statistics_action_id", "action_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    action_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("actions.id", onupdate="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
