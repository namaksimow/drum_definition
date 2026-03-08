"""add nickname to users

Revision ID: 0002_add_users_nickname
Revises: 0001_initial_schema
Create Date: 2026-03-08
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_users_nickname"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("nickname", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE users
            SET nickname = split_part(email, '@', 1)
            WHERE nickname IS NULL OR btrim(nickname) = ''
            """
        )
    )
    op.alter_column("users", "nickname", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "nickname")
