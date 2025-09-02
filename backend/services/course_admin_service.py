from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from backend.database import DB_PATH
from backend.models.course import Course


class CourseAdminService:
    """CRUD operations for courses stored in SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_target TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    prerequisites TEXT,
                    prestige INTEGER NOT NULL DEFAULT 0
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def list_courses(self) -> List[Course]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, skill_target, duration, prerequisites, prestige FROM courses"
            )
            rows = cur.fetchall()
        courses: List[Course] = []
        for row in rows:
            prereqs = json.loads(row[3]) if row[3] else None
            courses.append(
                Course(
                    id=row[0],
                    skill_target=row[1],
                    duration=row[2],
                    prerequisites=prereqs,
                    prestige=bool(row[4]),
                )
            )
        return courses

    # ------------------------------------------------------------------
    def create_course(self, course: Course) -> Course:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO courses (skill_target, duration, prerequisites, prestige) VALUES (?, ?, ?, ?)",
                (
                    course.skill_target,
                    course.duration,
                    json.dumps(course.prerequisites) if course.prerequisites else None,
                    int(course.prestige),
                ),
            )
            course_id = cur.lastrowid
            conn.commit()
        return Course(
            id=course_id,
            skill_target=course.skill_target,
            duration=course.duration,
            prerequisites=course.prerequisites,
            prestige=course.prestige,
        )

    # ------------------------------------------------------------------
    def update_course(self, course_id: int, **changes) -> Course:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT skill_target, duration, prerequisites, prestige FROM courses WHERE id = ?",
                (course_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("course_not_found")
            skill_target = changes.get("skill_target", row[0])
            duration = changes.get("duration", row[1])
            prerequisites = changes.get(
                "prerequisites", json.loads(row[2]) if row[2] else None
            )
            prestige = changes.get("prestige", bool(row[3]))
            cur.execute(
                """
                UPDATE courses
                SET skill_target = ?, duration = ?, prerequisites = ?, prestige = ?
                WHERE id = ?
                """,
                (
                    skill_target,
                    duration,
                    json.dumps(prerequisites) if prerequisites else None,
                    int(prestige),
                    course_id,
                ),
            )
            conn.commit()
        return Course(
            id=course_id,
            skill_target=skill_target,
            duration=duration,
            prerequisites=prerequisites,
            prestige=prestige,
        )

    # ------------------------------------------------------------------
    def delete_course(self, course_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()


course_admin_service = CourseAdminService()

__all__ = ["CourseAdminService", "course_admin_service"]
