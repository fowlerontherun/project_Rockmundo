"""Simple SQLite migration runner for Rockmundo.

This module applies SQL files stored in the ``migrations`` directory in
filename order.  A ``schema_migrations`` table tracks which scripts have
been executed so migrations are idempotent.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"
MIGRATIONS_DIR = Path(__file__).resolve() / "migrations"


def _iter_migrations() -> Iterable[Path]:
    """Yield migration files in sorted order."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def apply_migrations(db_path: Path | None = None) -> None:
    """Apply any pending migrations to the SQLite database.

    Parameters
    ----------
    db_path:
        Optional path to the SQLite database file.  When omitted, the default
        ``rockmundo.db`` alongside the backend package is used.
    """
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY)"
        )
        applied = {row[0] for row in cur.execute("SELECT filename FROM schema_migrations")}
        for migration in _iter_migrations():
            if migration.name in applied:
                continue
            cur.executescript(migration.read_text())
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (migration.name,),
            )
        conn.commit()
