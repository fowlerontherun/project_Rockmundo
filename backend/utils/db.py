# File: backend/utils/db.py

"""Asynchronous database helpers using :mod:`aiosqlite`.

This module exposes both asynchronous and synchronous helpers.  The
asynchronous interfaces (e.g. :func:`aget_conn`) should be preferred for all
new code.  The synchronous variants (``get_conn``, ``init_pool``,
``cached_query`` and the ``_Sync*`` classes) are retained only for legacy
callers and are **deprecated**.  They operate by driving the event loop
manually and will raise an error if invoked from within a running loop.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, Awaitable, Dict, List, Optional, Tuple

import aiosqlite

try:  # pragma: no cover - configuration is optional in tests
    from core.config import settings

    DEFAULT_DB = settings.database.path
except Exception:  # pragma: no cover - fallback for tests
    DEFAULT_DB = str(Path(__file__).resolve().parents[1] / "rockmundo.db")


# Connection pool -----------------------------------------------------------------
_pool: Optional[asyncio.Queue[aiosqlite.Connection]] = None


def _run(coro: Awaitable[Any]):
    """Execute ``coro`` respecting any existing event loop.

    If no loop is running, a temporary loop is created.  When a loop is
    already running, a ``RuntimeError`` is raised advising callers to use the
    asynchronous APIs instead.
    """

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:  # no current loop
        return asyncio.run(coro)
    if loop.is_running():
        raise RuntimeError(
            "Synchronous database helpers are deprecated inside a running loop; "
            "use async interfaces instead."
        )
    return loop.run_until_complete(coro)


async def _init_pool_async(db_path: Optional[str] = None, size: int = 5) -> None:
    """Create and populate the global connection pool.

    Parameters
    ----------
    db_path:
        Optional database path.  When omitted the default configuration is
        used.
    size:
        Number of connections to create in the pool.
    """

    global _pool
    if _pool is not None:  # Pool already initialised
        return

    path = str(db_path or DEFAULT_DB)
    queue: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=size)
    for _ in range(size):
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA busy_timeout = 5000;")
        await queue.put(conn)

    _pool = queue


def init_pool(db_path: Optional[str] = None, size: int = 5) -> None:
    """Initialise the connection pool synchronously.

    Deprecated: prefer awaiting :func:`_init_pool_async` directly.  This helper
    drives the event loop manually and will fail if called from within a running
    loop.
    """

    _run(_init_pool_async(db_path, size))


class _SyncCursor:
    """Deprecated synchronous wrapper around an ``aiosqlite`` cursor."""

    def __init__(self, cursor: aiosqlite.Cursor):
        self._cursor = cursor

    def execute(self, sql: str, params: Tuple[Any, ...] | List[Any] = ()):
        return _run(self._cursor.execute(sql, params))

    def executemany(self, sql: str, seq: List[Tuple[Any, ...]]):
        return _run(self._cursor.executemany(sql, seq))

    def fetchone(self):
        return _run(self._cursor.fetchone())

    def fetchall(self):
        return _run(self._cursor.fetchall())

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid


class _SyncConnection:
    """Deprecated synchronous facade for ``aiosqlite`` connections."""

    def __init__(self, path: str):
        self._conn = _run(aiosqlite.connect(path))
        self._conn.row_factory = aiosqlite.Row
        _run(self._conn.execute("PRAGMA foreign_keys = ON;"))
        _run(self._conn.execute("PRAGMA busy_timeout = 5000;"))

    def cursor(self) -> _SyncCursor:
        return _SyncCursor(self._conn.cursor())

    def execute(self, sql: str, params: Tuple[Any, ...] = ()):
        """Execute a query and return a synchronous cursor."""

        cursor = _run(self._conn.execute(sql, params))
        return _SyncCursor(cursor)

    def executemany(self, sql: str, seq: List[Tuple[Any, ...]]):  # pragma: no cover - passthrough
        return _run(self._conn.executemany(sql, seq))

    def executescript(self, script: str):  # pragma: no cover - passthrough
        return _run(self._conn.executescript(script))

    def commit(self) -> None:  # pragma: no cover - passthrough
        _run(self._conn.commit())

    def rollback(self) -> None:  # pragma: no cover - passthrough
        _run(self._conn.rollback())

    def close(self) -> None:  # pragma: no cover - passthrough
        _run(self._conn.close())

    # Context manager protocol -------------------------------------------------
    def __enter__(self) -> "_SyncConnection":  # pragma: no cover - passthrough
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - passthrough
        if exc_type is None:
            _run(self._conn.commit())
        else:
            _run(self._conn.rollback())
        _run(self._conn.close())


def get_conn(db_path: Optional[str] = None) -> _SyncConnection:
    """Return a synchronous ``aiosqlite`` connection.

    Deprecated: prefer :func:`aget_conn` and native ``async``/``await`` usage.
    This mirrors the old ``sqlite3.connect`` style API so existing code can
    operate without ``await`` while the underlying implementation uses the
    asynchronous driver.
    """

    path = str(db_path or DEFAULT_DB)
    return _SyncConnection(path)


@asynccontextmanager
async def aget_conn(db_path: Optional[str] = None):
    """Asynchronously yield a database connection.

    If a global pool has been initialised via :func:`init_pool` and no specific
    ``db_path`` is provided, connections are drawn from the pool.  Otherwise a
    new temporary connection is created and closed after use.
    """

    global _pool
    if db_path is None and _pool is not None:
        conn = await _pool.get()
        try:
            yield conn
            await conn.commit()
        except Exception:  # pragma: no cover - rollback on error
            await conn.rollback()
            raise
        finally:
            await _pool.put(conn)
    else:
        path = str(db_path or DEFAULT_DB)
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            yield conn
            await conn.commit()
        except Exception:  # pragma: no cover - rollback on error
            await conn.rollback()
            raise
        finally:
            await conn.close()


async def _cached_query_async(
    db_path: str, query: str, params: Tuple[Any, ...] = ()
) -> List[Dict[str, Any]]:
    async with aget_conn(db_path) as conn:
        cur = await conn.execute(query, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


@lru_cache(maxsize=128)
def cached_query(
    db_path: str, query: str, params: Tuple[Any, ...] = ()
) -> List[Dict[str, Any]]:
    """Execute a query and cache the results synchronously.

    Deprecated: prefer :func:`_cached_query_async`.
    """

    return _run(_cached_query_async(db_path, query, params))


__all__ = ["get_conn", "aget_conn", "cached_query", "init_pool"]

