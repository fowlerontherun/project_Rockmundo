import sqlite3

from services import fan_service
from services.image_training_service import ImageTrainingService
from services.skill_service import skill_service


def test_image_training_awards_xp(tmp_path):
    skill_service.db_path = tmp_path / "skills.db"
    skill_service._skills.clear()
    svc = ImageTrainingService(skill_service=skill_service)

    fashion = svc.attend_workshop(1, "fashion")
    assert fashion.xp == 40
    assert fashion.level == 1

    image_mgmt = svc.attend_course(1, "image_management")
    assert image_mgmt.xp == 100
    assert image_mgmt.level == 2


def test_image_skills_boost_fans(tmp_path, monkeypatch):
    db = tmp_path / "fans.db"
    monkeypatch.setattr(fan_service, "DB_PATH", db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE fans (user_id INTEGER, band_id INTEGER, location TEXT, loyalty INTEGER, source TEXT)"
        )
        conn.commit()

    skill_service.db_path = tmp_path / "skills.db"
    skill_service._skills.clear()
    training = ImageTrainingService(skill_service=skill_service)

    # baseline
    result = fan_service.boost_fans_after_gig(1, "NY", 100)
    assert result["fans_boosted"] == 10

    # train skills to level 3 (200 XP)
    for _ in range(5):
        training.attend_workshop(1, "fashion")
    for _ in range(2):
        training.attend_course(1, "image_management")

    result = fan_service.boost_fans_after_gig(1, "NY", 100)
    assert result["fans_boosted"] == 12

