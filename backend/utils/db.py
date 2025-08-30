# File: backend/utils/db.py
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, Any, List, Dict
from functools import lru_cache
from queue import Queue

try:
    from core.config import settings
    DEFAULT_DB = settings.DB_PATH
except Exception:
    DEFAULT_DB = str(Path(__file__).resolve().parents[1] / "rockmundo.db")

_WAL_INITIALISED = False
_POOLS: Dict[str, Queue[sqlite3.Connection]] = {}
_SQLITE_CONNECT = sqlite3.connect  # keep reference to the real connect


def init_pool(db_path: Optional[str] = None, size: int = 5) -> None:
    """Initialise a connection pool for the given database."""

    global _POOLS, _WAL_INITIALISED
    path = str(db_path or DEFAULT_DB)
    if path in _POOLS:
        return

    pool = Queue(maxsize=size)
    for _ in range(size):
        conn = _SQLITE_CONNECT(path, timeout=5.0, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute("PRAGMA busy_timeout = 5000;")
        if not _WAL_INITIALISED:
            try:
                cur.execute("PRAGMA journal_mode = WAL;")
            except Exception:
                pass
            _WAL_INITIALISED = True
        pool.put(conn)
    _POOLS[path] = pool


class PooledConnection:
    """Lightweight wrapper returning connections to the pool on close."""

    def __init__(self, conn: sqlite3.Connection, pool: Queue[sqlite3.Connection]):
        object.__setattr__(self, "_conn", conn)
        object.__setattr__(self, "_pool", pool)

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - passthrough
        return getattr(self._conn, name)

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover - passthrough
        setattr(self._conn, name, value)

    def close(self) -> None:
        # Instead of closing, return connection to the pool
        self._pool.put(self._conn)

    # Context manager support
    def __enter__(self) -> "PooledConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self.close()


def get_conn(db_path: Optional[str] = None, *args: Any, **kwargs: Any) -> sqlite3.Connection:
    """Acquire a connection from the pool.

    Extra positional/keyword arguments are ignored but accepted so that this
    function can transparently replace ``sqlite3.connect``.
    """

    if db_path is None and args:
        db_path = args[0]

    path = str(db_path or DEFAULT_DB)
    if path not in _POOLS:
        init_pool(path)
    pool = _POOLS[path]
    conn = pool.get()
    return PooledConnection(conn, pool)


# Monkey patch sqlite3.connect so legacy code also uses the pool
sqlite3.connect = get_conn  # type: ignore[assignment]


@lru_cache(maxsize=128)
def cached_query(
    db_path: str,
    query: str,
    params: Tuple[Any, ...] = (),
) -> List[Dict[str, Any]]:
    """Execute a query and cache the results."""

    with get_conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
