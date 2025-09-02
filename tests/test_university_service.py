import sqlite3
from pathlib import Path

from backend.services.university_service import UniversityService
from backend.services.skill_service import SkillService


def _setup_course(db: Path) -> None:
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO courses (skill_target, duration, prerequisites, prestige) VALUES (?, ?, ?, ?)",
            ("guitar", 1, '{"min_skill_level":1,"min_gpa":2.0}', 0),
        )
        conn.commit()


def test_enrollment_and_completion_awards_xp(tmp_path: Path) -> None:
    db = tmp_path / "uni.db"
    skill_svc = SkillService(db_path=db)
    uni = UniversityService(db_path=db, skill_service=skill_svc)
    _setup_course(db)

    uni.enroll(1, 1, skill_level=1, gpa=3.0)
    uni.advance(1, 1, weeks=1)

    skill = skill_svc._skills[(1, 1)]
    assert skill.xp > 0


def test_enrollment_rejects_if_requirements_not_met(tmp_path: Path) -> None:
    db = tmp_path / "uni.db"
    skill_svc = SkillService(db_path=db)
    uni = UniversityService(db_path=db, skill_service=skill_svc)
    _setup_course(db)

    try:
        uni.enroll(2, 1, skill_level=0, gpa=1.0)
    except ValueError:
        pass
    else:
        assert False, "expected ValueError"
