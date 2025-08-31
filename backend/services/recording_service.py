from __future__ import annotations

from typing import Dict, List, Optional

from backend.models.recording_session import RecordingSession
from backend.services.economy_service import EconomyError, EconomyService


class RecordingService:
    """In-memory management of studio recording sessions."""

    def __init__(self, economy: Optional[EconomyService] = None) -> None:
        self.economy = economy or EconomyService()
        try:  # ensure economy tables exist
            self.economy.ensure_schema()
        except Exception:
            pass
        self.sessions: Dict[int, RecordingSession] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    def schedule_session(
        self,
        band_id: int,
        studio: str,
        start: str,
        end: str,
        tracks: List[int],
        cost_cents: int,
    ) -> RecordingSession:
        """Schedule a new recording session and charge the band."""

        try:
            self.economy.withdraw(band_id, cost_cents)
        except EconomyError as e:
            raise ValueError(str(e)) from e
        session = RecordingSession(
            id=self._id_seq,
            band_id=band_id,
            studio=studio,
            start=start,
            end=end,
            track_statuses={tid: "pending" for tid in tracks},
            cost_cents=cost_cents,
        )
        self.sessions[session.id] = session
        self._id_seq += 1
        return session

    def assign_personnel(self, session_id: int, user_id: int) -> None:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError("session_not_found")
        if user_id not in session.personnel:
            session.personnel.append(user_id)

    def update_track_status(self, session_id: int, track_id: int, status: str) -> None:
        session = self.sessions.get(session_id)
        if not session:
            raise KeyError("session_not_found")
        session.track_statuses[track_id] = status

    def get_session(self, session_id: int) -> Optional[RecordingSession]:
        return self.sessions.get(session_id)

    def list_sessions(self, band_id: Optional[int] = None) -> List[RecordingSession]:
        if band_id is None:
            return list(self.sessions.values())
        return [s for s in self.sessions.values() if s.band_id == band_id]

    def delete_session(self, session_id: int) -> None:
        self.sessions.pop(session_id, None)


recording_service = RecordingService()

__all__ = ["RecordingService", "recording_service"]
