"""add tags to course

Revision ID: 0003_add_course_tags
Revises: 0002_add_users_nickname
Create Date: 2026-03-12
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_course_tags"
down_revision = "0002_add_users_nickname"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE course ADD COLUMN IF NOT EXISTS tags text[] NOT NULL DEFAULT '{}'::text[]"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE course DROP COLUMN IF EXISTS tags"))
