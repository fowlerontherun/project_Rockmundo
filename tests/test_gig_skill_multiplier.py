import sqlite3
from pathlib import Path

from backend.services import gig_service as gs
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID


def _setup_db(path: Path) -> None:
    conn = sqlite3.connect(path)
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
    cur.execute(
        "CREATE TABLE band_members (band_id INTEGER, user_id INTEGER, role TEXT)"
    )
    conn.commit()
    conn.close()


def test_skill_multiplier_boosts_gig(monkeypatch, tmp_path):
    db = tmp_path / "gig.db"
    _setup_db(db)

    monkeypatch.setattr(gs, "DB_PATH", str(db))
    monkeypatch.setattr(
        gs.fan_service,
        "get_band_fan_stats",
        lambda _bid: {"total_fans": 400, "average_loyalty": 100},
    )
    monkeypatch.setattr(gs.fan_service, "boost_fans_after_gig", lambda *a, **k: None)
    monkeypatch.setattr(gs.random, "randint", lambda a, b: 0)

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO bands (id, fame) VALUES (1, 0)")
    conn.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (1, 1, 'guitar')"
    )
    conn.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (1, 2, 'drums')"
    )
    conn.commit()
    conn.close()

    gs.create_gig(1, "City", 1000, "2024-01-01", 10)
    skill_service._skills.clear()
    skill_service._xp_today.clear()
    low = gs.simulate_gig_result(1)

    gs.create_gig(1, "City", 1000, "2024-01-02", 10)
    skill_service._skills.clear()
    skill_service._xp_today.clear()
    perf = Skill(
        id=SKILL_NAME_TO_ID["performance"],
        name="performance",
        category="stage",
        xp=900,
        level=10,
    )
    guitar = Skill(
        id=SKILL_NAME_TO_ID["guitar"],
        name="guitar",
        category="instrument",
        xp=900,
        level=10,
    )
    drums = Skill(
        id=SKILL_NAME_TO_ID["drums"],
        name="drums",
        category="instrument",
        xp=900,
        level=10,
    )
    skill_service._skills[(1, perf.id)] = perf
    skill_service._skills[(1, guitar.id)] = guitar
    skill_service._skills[(2, perf.id)] = Skill(
        id=perf.id, name="performance", category="stage", xp=900, level=10
    )
    skill_service._skills[(2, drums.id)] = drums
    high = gs.simulate_gig_result(2)

    assert high["attendance"] > low["attendance"]
    assert high["fame_gain"] > low["fame_gain"]
