import sqlite3
from pathlib import Path

from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID


def _setup_gig_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER DEFAULT 0)"
    )
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


def test_gig_performance_grants_skill(monkeypatch, tmp_path):
    from backend.services import gig_service as gs

    db = tmp_path / "gig.db"
    _setup_gig_db(db)
    monkeypatch.setattr(gs, "DB_PATH", str(db))
    monkeypatch.setattr(gs.fan_service, "get_band_fan_stats", lambda _bid: {"total_fans": 0, "average_loyalty": 0})
    monkeypatch.setattr(gs.fan_service, "boost_fans_after_gig", lambda *a, **k: None)

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO bands (id, fame) VALUES (1, 0)")
    conn.commit()
    conn.close()

    gs.create_gig(1, "Test City", 100, "2024-01-01", 10)

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    skill_service._method_history.clear()
    monkeypatch.setattr(skill_service, "_lifestyle_modifier", lambda _uid: 1.0)
    monkeypatch.setattr(skill_service.xp_events, "get_active_multiplier", lambda _n: 1.0)
    gs.simulate_gig_result(1)

    perf_skill = Skill(id=SKILL_NAME_TO_ID["performance"], name="performance", category="stage")
    inst = skill_service.train(1, perf_skill, 0)
    assert inst.xp == 20


class DummyEconomy:
    def ensure_schema(self) -> None:
        pass

    def withdraw(self, *args, **kwargs) -> None:
        pass


def test_recording_session_grants_skill():
    from backend.services.recording_service import RecordingService

    svc = RecordingService(economy=DummyEconomy())
    session = svc.schedule_session(1, "Studio", "2024-01-01", "2024-01-02", [1], 0)
    svc.assign_personnel(session.id, 42)

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    svc.update_track_status(session.id, 1, "mixed")

    prod_skill = Skill(id=SKILL_NAME_TO_ID["music_production"], name="music_production", category="creative")
    inst = skill_service.train(42, prod_skill, 0)
    assert inst.xp == 20
