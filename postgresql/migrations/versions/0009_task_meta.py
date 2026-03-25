"""add task result manifest and error columns

Revision ID: 0009_task_meta
Revises: 0008_author_req_admin_msg
Create Date: 2026-03-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009_task_meta"
down_revision = "0008_author_req_admin_msg"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE task
            ADD COLUMN IF NOT EXISTS result_manifest jsonb NOT NULL DEFAULT '{}'::jsonb
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE task
            ADD COLUMN IF NOT EXISTS error text
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE task
            DROP COLUMN IF EXISTS error
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE task
            DROP COLUMN IF EXISTS result_manifest
            """
        )
    )

