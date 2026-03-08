from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from app.config import get_settings


ROOT_DIR = Path(__file__).resolve().parent


def _safe_db_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Unsafe database name: {name}")
    return name


def create_database_if_not_exists() -> None:
    settings = get_settings()
    url = make_url(settings.database_url)
    if not url.database:
        raise ValueError("DATABASE_URL must include database name")

    db_name = _safe_db_name(url.database)
    admin_url = url.set(database="postgres")
    engine = create_engine(admin_url.render_as_string(hide_password=False), isolation_level="AUTOCOMMIT", future=True)

    with engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}).scalar()
        if exists:
            print(f"[create-db] Database already exists: {db_name}")
            return
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        print(f"[create-db] Database created: {db_name}")


def run_alembic(*args: str) -> None:
    cmd = [sys.executable, "-m", "alembic", *args]
    subprocess.run(cmd, cwd=ROOT_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="PostgreSQL service management")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("create-db", help="Create database if it does not exist")
    sub.add_parser("migrate", help="Apply migrations up to head")

    downgrade_parser = sub.add_parser("downgrade", help="Downgrade migrations")
    downgrade_parser.add_argument("-r", "--revision", required=True, help="Alembic revision, e.g. -1 or base")

    rev_parser = sub.add_parser("revision", help="Create new Alembic revision")
    rev_parser.add_argument("-m", "--message", required=True, help="Revision message")

    args = parser.parse_args()

    if args.command == "create-db":
        create_database_if_not_exists()
        return

    if args.command == "migrate":
        run_alembic("upgrade", "head")
        return

    if args.command == "downgrade":
        run_alembic("downgrade", args.revision)
        return

    if args.command == "revision":
        run_alembic("revision", "-m", args.message)
        return


if __name__ == "__main__":
    main()
