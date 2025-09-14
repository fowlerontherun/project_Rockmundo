import sqlite3
from pathlib import Path

import pytest

from models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services import gig_service as gs
from backend.services.skill_service import SkillService, skill_service
from backend.services.recording_service import RecordingService


class DummyEconomy:
    def __init__(self) -> None:
        self.schema_ensured = False
        self.withdraw_calls: list[tuple[int, int]] = []

    def ensure_schema(self) -> None:
        self.schema_ensured = True

    def withdraw(self, owner_id: int, amount: int) -> None:
        self.withdraw_calls.append((owner_id, amount))


def _setup_gig_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER DEFAULT 0)")
    cur.execute(
        """
        CREATE TABLE gigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue_size INTEGER,
            date TEXT,
            ticket_price INTEGER,
            status TEXT,
            attendance INTEGER,
            revenue INTEGER,
            fame_gain INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def test_get_category_multiplier() -> None:
    svc = SkillService()
    guitar = Skill(id=1, name="guitar", category="instrument")
    drums = Skill(id=2, name="drums", category="instrument")
    svc.train(1, guitar, 1000)
    svc.train(1, drums, 300)
    mult = svc.get_category_multiplier(1, "instrument")
    assert mult == pytest.approx(1 + ((11 + 4) / 2) / 200)


def test_gig_scaled_by_performance_skills(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db = tmp_path / "gig.db"
    _setup_gig_db(db)
    monkeypatch.setattr(gs, "DB_PATH", str(db))
    monkeypatch.setattr(
        gs.fan_service,
        "get_band_fan_stats",
        lambda _bid: {"total_fans": 100, "average_loyalty": 100},
    )
    monkeypatch.setattr(gs.fan_service, "boost_fans_after_gig", lambda *a, **k: None)
    monkeypatch.setattr(gs.random, "randint", lambda a, b: 0)

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO bands (id, fame) VALUES (1, 0)")
    conn.commit()
    conn.close()

    gs.create_gig(1, "City", 200, "2024-01-01", 10)
    gs.create_gig(1, "City", 200, "2024-02-01", 10)

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    base = gs.simulate_gig_result(1)

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    dance = Skill(id=SKILL_NAME_TO_ID["dance"], name="dance", category="performance")
    stage = Skill(
        id=SKILL_NAME_TO_ID["stage_presence"],
        name="stage_presence",
        category="performance",
    )
    skill_service.train(1, dance, 9900)
    skill_service.train(1, stage, 9900)
    skilled = gs.simulate_gig_result(2)

    assert skilled["attendance"] > base["attendance"]
    assert skilled["fame_gain"] > base["fame_gain"]


def test_recording_quality_scales_with_creative_skills() -> None:
    economy = DummyEconomy()
    svc = RecordingService(economy=economy)
    session = svc.schedule_session(1, "Studio", "2024-01-01", "2024-01-02", [1], 0)
    svc.assign_personnel(session.id, 1)
    skill_service._skills.clear()
    skill_service._xp_today.clear()
    svc.update_track_status(session.id, 1, "recorded")
    base_quality = session.track_quality[1]
    assert economy.schema_ensured is True
    assert economy.withdraw_calls == [(1, 0)]

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    prod = Skill(
        id=SKILL_NAME_TO_ID["music_production"],
        name="music_production",
        category="creative",
    )
    skill_service.train(1, prod, 9900)
    session2 = svc.schedule_session(1, "Studio", "2024-03-01", "2024-03-02", [2], 0)
    svc.assign_personnel(session2.id, 1)
    svc.update_track_status(session2.id, 2, "recorded")
    skilled_quality = session2.track_quality[2]

    assert skilled_quality > base_quality
