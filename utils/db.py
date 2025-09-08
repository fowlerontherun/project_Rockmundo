import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

@contextmanager
def get_conn(db_path: str | None = None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# Re-export asynchronous connection helper used in tests and services.
try:  # pragma: no cover - simple re-export wrapper
    from backend.utils.db import aget_conn  # type: ignore
except Exception:  # pragma: no cover
    aget_conn = None  # type: ignore

__all__ = ["get_conn", "aget_conn"]
