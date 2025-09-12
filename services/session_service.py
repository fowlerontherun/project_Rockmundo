from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class SessionService:
    """Service for tracking active sessions."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    ip TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    terminated INTEGER DEFAULT 0
                )
                """
            )
            conn.commit()

    def add_session(self, session_id: str, user_id: int, ip: str = "", user_agent: str = "") -> None:
        created = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (id, user_id, ip, user_agent, created_at, terminated)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (session_id, user_id, ip, user_agent, created),
            )
            conn.commit()

    def list_sessions(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, user_id, ip, user_agent, created_at FROM sessions WHERE terminated=0"
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "user_id": r[1],
                    "ip": r[2],
                    "user_agent": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]

    def terminate_session(self, session_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE sessions SET terminated=1 WHERE id=?", (session_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions")
            conn.commit()


session_service = SessionService()


def get_session_service() -> SessionService:
    return session_service
