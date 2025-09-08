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
        # Determine production quality multiplier from band skills
        prod = Skill(
            id=SKILL_NAME_TO_ID["music_production"],
            name="music_production",
            category="creative",
        )
        mixing = Skill(
            id=SKILL_NAME_TO_ID["mixing"],
            name="mixing",
            category="creative",
        )
        mastering = Skill(
            id=SKILL_NAME_TO_ID["mastering"],
            name="mastering",
            category="creative",
        )
        levels = [
            skill_service.train(band_id, prod, 0).level,
            skill_service.train(band_id, mixing, 0).level,
            skill_service.train(band_id, mastering, 0).level,
        ]
        avg_level = sum(levels) / len(levels)
        quality_mult = 1 + avg_level / 200

        # Apply multiplier: higher skill improves quality and reduces cost
        environment_quality *= quality_mult
        cost_cents = int(cost_cents / quality_mult)

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
            track_quality={tid: environment_quality for tid in tracks},
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

        # Adjust quality based on production skills for mixing/mastering
        if status in {"mixed", "mastered"}:
            skill_name = "mixing" if status == "mixed" else "mastering"
            skill = Skill(
                id=SKILL_NAME_TO_ID[skill_name],
                name=skill_name,
                category="creative",
            )
            level = skill_service.train(session.band_id, skill, 0).level
            mult = 1 + level / 200
            session.environment_quality *= mult
            prev = session.track_quality.get(track_id, session.environment_quality)
            session.track_quality[track_id] = prev * mult

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
        # Scale track quality by creative skill levels
        if session.personnel:
            mults = [
                skill_service.get_category_multiplier(uid, "creative")
                for uid in session.personnel
            ]
            quality_mult = sum(mults) / len(mults)
        else:
            quality_mult = 1.0
        session.track_quality[track_id] = session.environment_quality * quality_mult

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
