"""Service layer for managing jam sessions and economy hooks."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Set

from backend.models.jam_session import AudioStream, JamSession
from backend.services.economy_service import EconomyService

STUDIO_RENTAL_CENTS = 100
PREMIUM_STREAM_CENTS = 25

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

logger = logging.getLogger(__name__)


class JamService:
    """Jam session management backed by SQLite for persistence."""

    def __init__(self, economy: Optional[EconomyService] = None, db_path: str | None = None):
        self.economy = economy or EconomyService()
        try:
            self.economy.ensure_schema()
        except Exception as exc:
            logger.exception("Failed to ensure economy schema")
            raise RuntimeError(f"failed to ensure economy schema: {exc}") from exc
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()
        self.invites: Dict[str, Set[int]] = {}
        self.participants: Dict[str, Set[int]] = {}

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jam_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS jam_streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    stream_id TEXT NOT NULL,
                    codec TEXT NOT NULL,
                    premium INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(session_id) REFERENCES jam_sessions(id)
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def create_session(self, host_id: int) -> JamSession:
        """Create a new session and charge the host studio rental."""
        self.economy.withdraw(host_id, STUDIO_RENTAL_CENTS)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jam_sessions(host_id, created_at) VALUES (?, datetime('now'))",
                (host_id,),
            )
            session_id = str(cur.lastrowid)
            conn.commit()
        self.participants[session_id] = {host_id}
        self.invites[session_id] = set()
        return JamSession(id=session_id, host_id=host_id)

    def invite(self, session_id: str, inviter_id: int, invitee_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT host_id FROM jam_sessions WHERE id = ?", (session_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError("session_not_found")
        host_id = row[0]
        if inviter_id != host_id and inviter_id not in self.participants.get(session_id, set()):
            raise PermissionError("not_participant")
        self.invites.setdefault(session_id, set()).add(invitee_id)

    def join_session(self, session_id: str, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT host_id FROM jam_sessions WHERE id = ?", (session_id,))
            row = cur.fetchone()
        if not row:
            raise KeyError("session_not_found")
        host_id = row[0]
        if user_id != host_id and user_id not in self.invites.get(session_id, set()):
            raise PermissionError("not_invited")
        self.participants.setdefault(session_id, set()).add(user_id)

    def leave_session(self, session_id: str, user_id: int) -> None:
        parts = self.participants.get(session_id)
        if not parts:
            return
        parts.discard(user_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM jam_streams WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            if not parts:
                cur.execute("DELETE FROM jam_sessions WHERE id = ?", (session_id,))
                cur.execute("DELETE FROM jam_streams WHERE session_id = ?", (session_id,))
            conn.commit()
        if not parts:
            self.participants.pop(session_id, None)
            self.invites.pop(session_id, None)

    def start_stream(
        self, session_id: str, user_id: int, stream_id: str, codec: str, premium: bool = False
    ) -> AudioStream:
        if user_id not in self.participants.get(session_id, set()):
            raise PermissionError("not_participant")
        stream = AudioStream(user_id=user_id, stream_id=stream_id, codec=codec, premium=premium)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jam_streams(session_id, user_id, stream_id, codec, premium, started_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, user_id, stream_id, codec, int(premium), stream.started_at),
            )
            conn.commit()
        if premium:
            self.economy.withdraw(user_id, PREMIUM_STREAM_CENTS)
        return stream

    def stop_stream(self, session_id: str, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM jam_streams WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            conn.commit()
