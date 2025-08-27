"""Service layer for managing jam sessions and economy hooks."""
from __future__ import annotations

from typing import Dict, Optional

from backend.models.jam_session import AudioStream, JamSession
from backend.services.economy_service import EconomyService

STUDIO_RENTAL_CENTS = 100
PREMIUM_STREAM_CENTS = 25


class JamService:
    """Simple in-memory jam session management."""

    def __init__(self, economy: Optional[EconomyService] = None):
        self.economy = economy or EconomyService()
        try:
            self.economy.ensure_schema()
        except Exception:
            pass
        self.sessions: Dict[str, JamSession] = {}
        self._session_seq = 0

    # ------------------------------------------------------------------
    def create_session(self, host_id: int) -> JamSession:
        """Create a new session and charge the host studio rental."""
        self.economy.withdraw(host_id, STUDIO_RENTAL_CENTS)
        self._session_seq += 1
        session_id = str(self._session_seq)
        session = JamSession(id=session_id, host_id=host_id)
        session.add_participant(host_id)
        self.sessions[session_id] = session
        return session

    def invite(self, session_id: str, inviter_id: int, invitee_id: int) -> None:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError("session_not_found")
        if inviter_id != session.host_id and inviter_id not in session.participants:
            raise PermissionError("not_participant")
        session.invites.add(invitee_id)

    def join_session(self, session_id: str, user_id: int) -> None:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError("session_not_found")
        if user_id != session.host_id and user_id not in session.invites:
            raise PermissionError("not_invited")
        session.add_participant(user_id)

    def leave_session(self, session_id: str, user_id: int) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return
        session.remove_participant(user_id)
        if not session.participants:
            self.sessions.pop(session_id, None)

    def start_stream(
        self, session_id: str, user_id: int, stream_id: str, codec: str, premium: bool = False
    ) -> AudioStream:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError("session_not_found")
        if user_id not in session.participants:
            raise PermissionError("not_participant")
        stream = AudioStream(user_id=user_id, stream_id=stream_id, codec=codec, premium=premium)
        session.streams[user_id] = stream
        if premium:
            self.economy.withdraw(user_id, PREMIUM_STREAM_CENTS)
        return stream

    def stop_stream(self, session_id: str, user_id: int) -> None:
        session = self.sessions.get(session_id)
        if not session:
            return
        session.streams.pop(user_id, None)
