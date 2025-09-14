"""University service for managing course enrollments and progress."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List

from backend.database import DB_PATH
from backend.models.course import Course
from backend.models.skill import Skill
from services.skill_service import SkillService
from backend.seeds.skill_seed import SKILL_NAME_TO_ID


class UniversityService:
    """Manage course enrollments and semester progression."""

    def __init__(self, db_path: Path | None = None, skill_service: SkillService | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.skill_service = skill_service or SkillService(db_path=db_path)
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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    enrolled_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(course_id) REFERENCES courses(id)
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def list_courses(self) -> List[Course]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, skill_target, duration, prerequisites, prestige FROM courses")
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
    def enroll(self, user_id: int, course_id: int, skill_level: int, gpa: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT skill_target, duration, prerequisites, prestige FROM courses WHERE id = ?",
                (course_id,),
            )
            row = cur.fetchone()
        if not row:
            raise ValueError("course_not_found")
        prereqs = json.loads(row[2]) if row[2] else {}
        min_skill = prereqs.get("min_skill_level", 0)
        min_gpa = prereqs.get("min_gpa", 0.0)
        if skill_level < min_skill or gpa < min_gpa:
            raise ValueError("entrance_requirements_not_met")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO enrollments(user_id, course_id, progress, completed, enrolled_at) "
                "VALUES (?, ?, 0, 0, datetime('now'))",
                (user_id, course_id),
            )
            conn.commit()

    # ------------------------------------------------------------------
    def advance(self, user_id: int, course_id: int, weeks: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT progress, completed FROM enrollments WHERE user_id = ? AND course_id = ?",
                (user_id, course_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("not_enrolled")
            progress, completed = row
            if completed:
                return
            cur.execute("SELECT duration, skill_target FROM courses WHERE id = ?", (course_id,))
            crow = cur.fetchone()
            duration, skill_target = crow[0], crow[1]
            progress += weeks
            done = progress >= duration
            cur.execute(
                "UPDATE enrollments SET progress = ?, completed = ? WHERE user_id = ? AND course_id = ?",
                (progress, int(done), user_id, course_id),
            )
            conn.commit()
        if done:
            skill_id = SKILL_NAME_TO_ID.get(skill_target, course_id)
            skill = Skill(id=skill_id, name=skill_target, category="academic")
            self.skill_service.train(user_id, skill, duration * 100)


__all__ = ["UniversityService"]
