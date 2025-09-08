from __future__ import annotations

from typing import Dict, List, Optional

from backend.models.learning_method import LearningMethod
from backend.models.recording_session import RecordingSession
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.chemistry_service import ChemistryService
from backend.services.economy_service import EconomyError, EconomyService
from backend.services.skill_service import skill_service


class RecordingService:
    """In-memory management of studio recording sessions."""

    def __init__(
        self,
        economy: Optional[EconomyService] = None,
        chemistry_service: ChemistryService | None = None,
    ) -> None:
        self.economy = economy or EconomyService()
        try:  # ensure economy tables exist
            self.economy.ensure_schema()
        except Exception:
            pass
        self.chemistry_service = chemistry_service or ChemistryService()
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
        environment_quality: float = 1.0,
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
            environment_quality=environment_quality,
        )
        avg = 50.0
        if session.personnel:
            scores = []
            for i, a in enumerate(session.personnel):
                for b in session.personnel[i + 1 :]:
                    pair = self.chemistry_service.initialize_pair(a, b)
                    scores.append(pair.score)
            if scores:
                avg = sum(scores) / len(scores)
                session.environment_quality *= 1 + (avg - 50) / 100
        session.chemistry_avg = avg
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

        if session.personnel:
            scores = []
            for i, a in enumerate(session.personnel):
                for b in session.personnel[i + 1 :]:
                    pair = self.chemistry_service.adjust_pair(a, b, 1)
                    scores.append(pair.score)
            if scores:
                avg = sum(scores) / len(scores)
                session.environment_quality *= 1 + (avg - 50) / 100
                session.chemistry_avg = avg

        # Award practice XP to all personnel based on task difficulty
        difficulty = {"recorded": 1, "mixed": 2, "mastered": 3}.get(status, 1)
        skill = Skill(
            id=SKILL_NAME_TO_ID["music_production"],
            name="music_production",
            category="creative",
        )
        for uid in session.personnel:
            skill_service.train_with_method(uid, skill, LearningMethod.PRACTICE, difficulty)

    # ------------------------------------------------------------------
    def practice_skill(
        self,
        user_id: int,
        skill_name: str,
        amount: int,
        method: LearningMethod = LearningMethod.PRACTICE,
        environment_quality: float = 1.0,
    ) -> Skill:
        """Award XP toward a specific music production skill."""
        if skill_name not in SKILL_NAME_TO_ID:
            raise KeyError("skill_not_found")
        skill = Skill(
            id=SKILL_NAME_TO_ID[skill_name],
            name=skill_name,
            category="creative",
            parent_id=SKILL_NAME_TO_ID.get("music_production"),
        )
        return skill_service.train_with_method(
            user_id,
            skill,
            method,
            amount,
            environment_quality=environment_quality,
        )

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
