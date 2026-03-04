"""initial schema from create_db.sql

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-04
"""
from __future__ import annotations

from pathlib import Path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _load_schema_sql() -> str:
    migration_file = Path(__file__).resolve()
    schema_path = migration_file.parents[2] / "create_db.sql"
    sql_text = schema_path.read_text(encoding="utf-8")

    # create_db.sql already wraps everything in transaction.
    # Alembic manages transaction itself, so we strip BEGIN/COMMIT.
    sql_text = sql_text.replace("BEGIN;", "").replace("COMMIT;", "")
    return sql_text


def upgrade() -> None:
    sql_text = _load_schema_sql()
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]
    for stmt in statements:
        op.execute(sa.text(stmt))


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute(sa.text("DROP TABLE IF EXISTS statistics CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS tablature_comments CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS tablature_reactions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course_comments CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course_reactions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS tablatures CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS task CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS course CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS tracks CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS users CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS actions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS status CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS visibilities CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS roles CASCADE"))

