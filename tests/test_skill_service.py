import sqlite3
from pathlib import Path

from backend.models.skill import Skill
from backend.models.xp_config import XPConfig, get_config, set_config
from backend.services.skill_service import SkillService


class DummyXPEvents:
    def __init__(self, mult: float):
        self.mult = mult

    def get_active_multiplier(self, skill: str | None = None) -> float:  # pragma: no cover - simple proxy
        return self.mult


def _setup_db(tmp_path: Path, modifier: float) -> Path:
    db = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE xp_modifiers (user_id INTEGER, modifier REAL, date TEXT)")
    cur.execute(
        "INSERT INTO xp_modifiers (user_id, modifier, date) VALUES (1, ?, '2024-01-01')",
        (modifier,),
    )
    conn.commit()
    conn.close()
    return db


def test_skill_gain_with_modifiers(tmp_path: Path) -> None:
    db = _setup_db(tmp_path, 1.5)
    svc = SkillService(xp_events=DummyXPEvents(2.0), db_path=db)
    skill = Skill(id=1, name="guitar", category="instrument")

    updated = svc.train(1, skill, 10)
    assert updated.xp == 30
    assert updated.level == 1

    updated = svc.train(1, skill, 40)
    assert updated.xp == 150
    assert updated.level == 2


def test_skill_daily_cap() -> None:
    old_cfg = get_config()
    set_config(XPConfig(daily_cap=100))
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=2, name="drums", category="instrument")

    svc.train(1, skill, 80)
    updated = svc.train(1, skill, 50)

    assert updated.xp == 100
    assert updated.level == 2
    set_config(old_cfg)


def test_skill_decay() -> None:
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=3, name="vocals", category="performance")

    svc.train(1, skill, 120)
    updated = svc.apply_decay(1, 3, 30)

    assert updated.xp == 90
    assert updated.level == 1

