from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from database import DB_PATH
from backend.models.apprenticeship import Apprenticeship
from backend.services.karma_service import KarmaService


class ApprenticeshipService:
    """Manage apprenticeship lifecycle and XP rewards."""

    def __init__(self, db_path: Path | None = None, karma: KarmaService | None = None) -> None:
        self.db_path = Path(db_path or DB_PATH)
        self.karma = karma

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    def request(
        self,
        student_id: int,
        mentor_id: int,
        mentor_type: str,
        skill_id: int,
        duration_days: int,
        level_requirement: int = 0,
    ) -> Apprenticeship:
        """Record an apprenticeship request waiting for mentor approval."""

        app = Apprenticeship(
            id=None,
            student_id=student_id,
            mentor_id=mentor_id,
            mentor_type=mentor_type,
            skill_id=skill_id,
            duration_days=duration_days,
            level_requirement=level_requirement,
            status="pending",
        )
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO apprenticeships (student_id, mentor_id, mentor_type, skill_id, duration_days, level_requirement, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    app.student_id,
                    app.mentor_id,
                    app.mentor_type,
                    app.skill_id,
                    app.duration_days,
                    app.level_requirement,
                    app.status,
                ),
            )
            app.id = cur.lastrowid
            conn.commit()
        return app

    def start(self, apprenticeship_id: int) -> None:
        """Activate an apprenticeship after mentor approval."""

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE apprenticeships SET start_date = ?, status = 'active' WHERE id = ?",
                (datetime.utcnow().isoformat(), apprenticeship_id),
            )
            conn.commit()

    def stop(self, apprenticeship_id: int, mentor_level: int, relationship: int) -> int:
        """Complete an apprenticeship and return XP gained."""

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT student_id, mentor_id, skill_id, duration_days FROM apprenticeships WHERE id = ?",
                (apprenticeship_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("apprenticeship not found")
            student_id, mentor_id, _skill_id, duration_days = row
            xp = self.compute_xp(mentor_level, relationship, duration_days)
            cur.execute(
                "UPDATE apprenticeships SET status = 'completed' WHERE id = ?",
                (apprenticeship_id,),
            )
            conn.commit()

        if self.karma:
            self.karma.adjust_karma(mentor_id, +2, "apprenticeship", "mentor", grant_xp=False)
            self.karma.adjust_karma(student_id, +1, "apprenticeship", "student", grant_xp=False)
        return xp

    # ------------------------------------------------------------------
    @staticmethod
    def compute_xp(mentor_level: int, relationship: int, duration_days: int) -> int:
        """Basic XP formula based on mentor level and relationship."""

        base = mentor_level * duration_days
        multiplier = 1 + (relationship / 100)
        return int(base * multiplier)


__all__ = ["ApprenticeshipService"]
