import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from backend.seeds.skill_seed import SEED_SKILLS
from models.learning_method import METHOD_PROFILES, LearningMethod
from backend.services import fan_interaction_service, fan_service
from backend.services.image_training_service import (
    Stylist,
    StylistService,
    study_image_tutorial,
)
from backend.services.skill_service import SkillService
from backend.services.economy_service import EconomyService


FASHION_SKILL = next(s for s in SEED_SKILLS if s.name == "fashion")
IMAGE_MANAGEMENT_SKILL = next(s for s in SEED_SKILLS if s.name == "image_management")


def _setup_fan_db(tmp_path, monkeypatch):
    db = tmp_path / "fans.sqlite"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE fan_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            fan_id INTEGER,
            interaction_type TEXT,
            content TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE fans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            band_id INTEGER,
            location TEXT,
            loyalty INTEGER,
            source TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    # Patch DB paths
    monkeypatch.setattr(fan_interaction_service, "DB_PATH", db)
    monkeypatch.setattr(fan_service, "DB_PATH", db)
    monkeypatch.setattr(
        fan_service, "avatar_service", SimpleNamespace(get_avatar=lambda _: None)
    )
    return db


def test_image_skills_increase_fans(tmp_path, monkeypatch):
    _setup_fan_db(tmp_path, monkeypatch)
    skills = SkillService()
    monkeypatch.setattr(fan_interaction_service, "skill_service", skills)
    monkeypatch.setattr(
        "backend.services.image_training_service.skill_service", skills
    )
    monkeypatch.setattr(skills, "_has_item", lambda *args, **kwargs: True)

    fan_interaction_service.record_interaction(1, 1, "post", "hello")
    conn = sqlite3.connect(fan_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fans")
    assert cur.fetchone()[0] == 0
    conn.close()

    study_image_tutorial(1, FASHION_SKILL, 10)
    study_image_tutorial(1, IMAGE_MANAGEMENT_SKILL, 10)

    result = fan_interaction_service.record_interaction(
        1, 2, "photo_op", "stylish"
    )
    assert result["fans_gained"] > 0
    conn = sqlite3.connect(fan_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fans")
    fans = cur.fetchone()[0]
    conn.close()
    assert fans == result["fans_gained"]


def test_stylist_training_session(tmp_path, monkeypatch):
    economy = EconomyService(db_path=tmp_path / "econ.sqlite")
    economy.ensure_schema()
    skills = SkillService()
    svc = StylistService(economy, skills)
    stylist = svc.create_stylist(
        Stylist(id=None, name="Aiko", specialization="fashion", hourly_rate=50)
    )
    monkeypatch.setattr(skills, "_has_item", lambda *args, **kwargs: True)

    economy.deposit(1, 10000)
    skills.train(1, FASHION_SKILL, 1400)

    balance_before = economy.get_balance(1)
    result = svc.schedule_session(1, FASHION_SKILL, stylist.id, 2)
    balance_after = economy.get_balance(1)

    assert balance_after == balance_before - stylist.hourly_rate * 2
    assert (
        result["xp_gained"]
        == METHOD_PROFILES[LearningMethod.TUTOR].xp_per_hour * 2
    )

