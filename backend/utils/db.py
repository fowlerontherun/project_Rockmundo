# File: backend/utils/db.py
import sqlite3
from pathlib import Path
from typing import Optional

try:
    from core.config import settings
    DEFAULT_DB = settings.DB_PATH
except Exception:
    DEFAULT_DB = str(Path(__file__).resolve().parents[1] / "rockmundo.db")

_WAL_INITIALISED = False

def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    global _WAL_INITIALISED
    path = str(db_path or DEFAULT_DB)
    conn = sqlite3.connect(path, timeout=5.0, isolation_level=None)
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
    return conn
