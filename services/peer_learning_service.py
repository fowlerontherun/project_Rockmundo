"""Peer learning sessions granting XP based on band cohesion."""
from __future__ import annotations

import sqlite3
from typing import Iterable, List

from backend.database import DB_PATH
from models.skill import Skill
from backend.services.skill_service import skill_service
from seeds.skill_seed import SKILL_NAME_TO_ID


PERFORMANCE_SKILL = Skill(
    id=SKILL_NAME_TO_ID["performance"],
    name="performance",
    category="stage",
)


class PeerLearningService:
    """Coordinate peer learning sessions for bands."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)

    # ------------------------------------------------------------------
    def run_session(self, band_id: int, members: Iterable[int]) -> dict:
        """Award XP to members based on average skill and band cohesion."""

        member_list: List[int] = list(members)
        if not member_list:
            return {"xp_gain": 0}

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT cohesion FROM bands WHERE id = ?",
                (band_id,),
            ).fetchone()
        cohesion = row[0] if row else 1

        levels = []
        for m in member_list:
            inst = skill_service.train(m, PERFORMANCE_SKILL, 0)
            levels.append(inst.level)
        avg_level = sum(levels) / len(levels) if levels else 0

        gain = int(avg_level * cohesion)
        for m in member_list:
            skill_service.train(m, PERFORMANCE_SKILL, gain)
        return {"xp_gain": gain, "cohesion": cohesion}

    # ------------------------------------------------------------------
    def schedule_session(self, band_id: int, members: Iterable[int], run_at: str) -> dict:
        """Schedule a peer learning session via the scheduler service."""
        from services.scheduler_service import schedule_task

        member_list = list(members)
        try:
            return schedule_task(
                "peer_learning", {"band_id": band_id, "members": member_list}, run_at
            )
        except sqlite3.OperationalError:
            # scheduler tables may not be set up in minimal test environments
            return {"status": "skipped"}


peer_learning_service = PeerLearningService()


def run_scheduled_session(band_id: int, members: List[int]) -> dict:
    """Scheduler hook to execute a peer session."""
    return peer_learning_service.run_session(band_id, members)
