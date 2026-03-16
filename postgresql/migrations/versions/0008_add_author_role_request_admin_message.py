"""add admin message to author role requests

Revision ID: 0008_author_req_admin_msg
Revises: 0007_seed_admin_user
Create Date: 2026-03-15
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_author_req_admin_msg"
down_revision = "0007_seed_admin_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE author_role_requests
            ADD COLUMN IF NOT EXISTS admin_message text
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE author_role_requests
            DROP COLUMN IF EXISTS admin_message
            """
        )
    )
