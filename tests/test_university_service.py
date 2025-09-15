import sqlite3
from pathlib import Path
import sys
import pytest

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

from backend.services.university_service import UniversityService
from backend.services.skill_service import SkillService
from seeds.skill_seed import SKILL_NAME_TO_ID


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

    with pytest.raises(ValueError):
        uni.enroll(2, 1, skill_level=0, gpa=1.0)


def test_ear_training_course_awards_xp(tmp_path: Path) -> None:
    db = tmp_path / "uni.db"
    skill_svc = SkillService(db_path=db)
    uni = UniversityService(db_path=db, skill_service=skill_svc)
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO courses (id, skill_target, duration, prerequisites, prestige) VALUES (?, ?, ?, ?, ?)",
            (
                SKILL_NAME_TO_ID["ear_training"],
                "ear_training",
                1,
                '{"min_skill_level":1,"min_gpa":2.0}',
                0,
            ),
        )
        conn.commit()

    course_id = SKILL_NAME_TO_ID["ear_training"]
    uni.enroll(1, course_id, skill_level=1, gpa=3.0)
    uni.advance(1, course_id, weeks=1)

    skill = skill_svc._skills[(1, course_id)]
    assert skill.xp > 0
