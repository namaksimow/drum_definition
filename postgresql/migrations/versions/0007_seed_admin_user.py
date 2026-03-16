"""seed admin user

Revision ID: 0007_seed_admin_user
Revises: 0006_add_author_role_requests
Create Date: 2026-03-13
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_seed_admin_user"
down_revision = "0006_add_author_role_requests"
branch_labels = None
depends_on = None

_ADMIN_EMAIL = "admin@mail.ru"
_ADMIN_NICKNAME = "admin"
_ADMIN_PASSWORD_HASH = "pbkdf2_sha256$200000$XY6wBwrEjdh9NrFFyYugJw==$UU4MMxECQW46wOoaEtFNduwZh8nXUhT+bOw9KATI+UU="


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO roles(role_title)
            SELECT 'admin'
            WHERE NOT EXISTS (
                SELECT 1 FROM roles WHERE lower(role_title) = 'admin'
            )
            """
        )
    )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO users(email, nickname, password_hash, role_id)
            SELECT :email, :nickname, :password_hash, r.id
            FROM roles r
            WHERE lower(r.role_title) = 'admin'
              AND NOT EXISTS (
                SELECT 1 FROM users u WHERE lower(u.email) = lower(:email)
              )
            """
        ),
        {
            "email": _ADMIN_EMAIL,
            "nickname": _ADMIN_NICKNAME,
            "password_hash": _ADMIN_PASSWORD_HASH,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM users
            WHERE lower(email) = lower(:email)
            """
        ),
        {"email": _ADMIN_EMAIL},
    )
