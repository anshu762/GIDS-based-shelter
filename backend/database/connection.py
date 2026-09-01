"""PostgreSQL connection helpers for the additive GIDS mobile API.

The existing dashboard and Modules 1–6 do not call this file. DATABASE_URL is
required only for /api/mobile/* endpoints, so the existing web dashboard keeps
working even before the Railway PostgreSQL plugin is provisioned.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


BACKEND_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_FILE = BACKEND_ROOT / "database" / "mobile_schema.sql"

_pool: ConnectionPool | None = None


def database_url() -> str | None:
    """Return Railway/local DATABASE_URL, normalized for Psycopg 3."""
    value = os.getenv("DATABASE_URL", "").strip()

    if not value:
        return None

    if value.startswith("postgres://"):
        return "postgresql://" + value[len("postgres://") :]

    return value


def database_is_configured() -> bool:
    """Return true only when DATABASE_URL is available."""
    return database_url() is not None


def get_pool() -> ConnectionPool:
    """Create the shared synchronous connection pool only when needed."""
    global _pool

    url = database_url()

    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Add Railway PostgreSQL and "
            "link it to the backend service before using /api/mobile endpoints."
        )

    if _pool is None:
        _pool = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=5,
            kwargs={
                "row_factory": dict_row,
            },
            open=True,
        )

    return _pool


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield one pooled PostgreSQL connection with commit/rollback handling."""
    with get_pool().connection() as connection:
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def run_mobile_migration() -> None:
    """Run the checked-in mobile schema migration safely and idempotently."""
    if not MIGRATION_FILE.exists():
        raise FileNotFoundError(
            f"Mobile migration file not found: {MIGRATION_FILE}"
        )

    migration_sql = MIGRATION_FILE.read_text(encoding="utf-8")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(migration_sql)


def close_pool() -> None:
    """Close PostgreSQL pool on FastAPI shutdown."""
    global _pool

    if _pool is not None:
        _pool.close()
        _pool = None