from __future__ import annotations

import sqlite3
from typing import List, Optional

from backend.database import DB_PATH
from backend.models.apprenticeship import Apprenticeship


class ApprenticeshipAdminService:
    """CRUD helpers for apprenticeship records."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS apprenticeships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    mentor_id INTEGER NOT NULL,
                    mentor_type TEXT NOT NULL,
                    skill_id INTEGER NOT NULL,
                    duration_days INTEGER NOT NULL,
                    level_requirement INTEGER NOT NULL,
                    start_date TEXT,
                    status TEXT NOT NULL
                )
                """,
            )
            conn.commit()

    def list_apprenticeships(self) -> List[Apprenticeship]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, student_id, mentor_id, mentor_type, skill_id, duration_days, level_requirement, start_date, status
                FROM apprenticeships ORDER BY id
                """
            )
            rows = cur.fetchall()
            return [Apprenticeship(**dict(row)) for row in rows]

    def create_apprenticeship(self, app: Apprenticeship) -> Apprenticeship:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO apprenticeships (student_id, mentor_id, mentor_type, skill_id, duration_days, level_requirement, start_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    app.student_id,
                    app.mentor_id,
                    app.mentor_type,
                    app.skill_id,
                    app.duration_days,
                    app.level_requirement,
                    app.start_date,
                    app.status,
                ),
            )
            app.id = cur.lastrowid
            conn.commit()
            return app

    def update_apprenticeship(self, app_id: int, **changes) -> Apprenticeship:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, student_id, mentor_id, mentor_type, skill_id, duration_days, level_requirement, start_date, status
                FROM apprenticeships WHERE id = ?
                """,
                (app_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Apprenticeship not found")
            data = dict(row)
            for k, v in changes.items():
                if k in data and v is not None:
                    data[k] = v
            cur.execute(
                """
                UPDATE apprenticeships
                SET student_id=?, mentor_id=?, mentor_type=?, skill_id=?, duration_days=?, level_requirement=?, start_date=?, status=?
                WHERE id=?
                """,
                (
                    data["student_id"],
                    data["mentor_id"],
                    data["mentor_type"],
                    data["skill_id"],
                    data["duration_days"],
                    data["level_requirement"],
                    data["start_date"],
                    data["status"],
                    app_id,
                ),
            )
            conn.commit()
            return Apprenticeship(**data)

    def delete_apprenticeship(self, app_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM apprenticeships WHERE id=?", (app_id,))
            conn.commit()

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM apprenticeships")
            conn.commit()


apprenticeship_admin_service = ApprenticeshipAdminService()


def get_apprenticeship_admin_service() -> ApprenticeshipAdminService:
    return apprenticeship_admin_service


__all__ = [
    "ApprenticeshipAdminService",
    "apprenticeship_admin_service",
    "get_apprenticeship_admin_service",
]
