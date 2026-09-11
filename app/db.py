"""PostgreSQL + pgvector connection helpers.

Single source of truth for how the app talks to the database. It:
  * builds connections from `settings.database_url`,
  * registers the pgvector adapter so Python lists map to `vector` columns
    (and rows come back as numpy/lists automatically), and
  * exposes a context-managed connection and a convenience `run` helper.

The service layer and MCP tools use these helpers rather than opening
connections themselves, so connection handling and vector registration live in
exactly one place.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from pgvector.psycopg import register_vector

from app.config import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield a psycopg connection with the pgvector adapter registered.

    Commits on clean exit, rolls back on exception, and always closes. Use for
    a unit of work:

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = psycopg.connect(settings.database_url)
    try:
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run(query: str, params: tuple[Any, ...] | None = None, *, fetch: str | None = None):
    """Execute a single query in its own connection.

    fetch: None -> return None; 'one' -> one row; 'all' -> list of rows.
    Rows are returned as dicts keyed by column name for convenient callers.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch is None:
                return None
            columns = [c.name for c in cur.description] if cur.description else []
            if fetch == "one":
                row = cur.fetchone()
                return dict(zip(columns, row)) if row else None
            if fetch == "all":
                return [dict(zip(columns, row)) for row in cur.fetchall()]
            raise ValueError(f"invalid fetch mode: {fetch!r}")


def healthcheck() -> bool:
    """Return True if the database is reachable and responds to a trivial query."""
    try:
        result = run("SELECT 1 AS ok", fetch="one")
        return bool(result and result.get("ok") == 1)
    except Exception:
        return False
