from __future__ import annotations

import sqlite3
from typing import List, Optional

from backend.database import DB_PATH
from models.tutor import Tutor


class TutorAdminService:
    """CRUD helpers for tutor records."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tutors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialization TEXT NOT NULL,
                    hourly_rate INTEGER NOT NULL,
                    level_requirement INTEGER NOT NULL
                )
                """,
            )
            conn.commit()

    def list_tutors(self) -> List[Tutor]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, specialization, hourly_rate, level_requirement FROM tutors ORDER BY id"
            )
            rows = cur.fetchall()
            return [Tutor(**dict(row)) for row in rows]

    def create_tutor(self, tutor: Tutor) -> Tutor:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tutors (name, specialization, hourly_rate, level_requirement) VALUES (?, ?, ?, ?)",
                (tutor.name, tutor.specialization, tutor.hourly_rate, tutor.level_requirement),
            )
            tutor.id = cur.lastrowid
            conn.commit()
            return tutor

    def update_tutor(self, tutor_id: int, **changes) -> Tutor:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, specialization, hourly_rate, level_requirement FROM tutors WHERE id = ?",
                (tutor_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Tutor not found")
            data = dict(row)
            for k, v in changes.items():
                if k in data and v is not None:
                    data[k] = v
            cur.execute(
                "UPDATE tutors SET name=?, specialization=?, hourly_rate=?, level_requirement=? WHERE id=?",
                (
                    data["name"],
                    data["specialization"],
                    data["hourly_rate"],
                    data["level_requirement"],
                    tutor_id,
                ),
            )
            conn.commit()
            return Tutor(**data)

    def delete_tutor(self, tutor_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tutors WHERE id=?", (tutor_id,))
            conn.commit()

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tutors")
            conn.commit()


tutor_admin_service = TutorAdminService()


def get_tutor_admin_service() -> TutorAdminService:
    return tutor_admin_service


__all__ = ["TutorAdminService", "tutor_admin_service", "get_tutor_admin_service"]
