import sqlite3

from backend.services import live_performance_service, live_performance_analysis
from backend.services.city_service import city_service
from backend.models.city import City
from backend.services.skill_service import skill_service
from backend.models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID


def test_skill_multiplier_boosts_crowd_and_fame(monkeypatch, tmp_path):
    city_service.cities.clear()
    city_service.add_city(
        City(
            name="Metro",
            population=1_000_000,
            style_preferences={},
            event_modifier=1.0,
            market_index=1.0,
        )
    )

    db_file = tmp_path / "gig.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)"
    )
    cur.execute(
        "CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)"
    )
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER, legacy_state TEXT, original_release_date TEXT)"
    )
    cur.execute(
        "CREATE TABLE band_members (band_id INTEGER, user_id INTEGER, role TEXT)"
    )
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (1, 100, 0, 0)")
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (2, 100, 0, 0)")
    cur.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (1, 1, 'guitar')"
    )
    cur.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (1, 2, 'drums')"
    )
    cur.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (2, 3, 'guitar')"
    )
    cur.execute(
        "INSERT INTO band_members (band_id, user_id, role) VALUES (2, 4, 'drums')"
    )
    cur.execute(
        "INSERT INTO songs (id, band_id, title, duration_sec, genre, play_count, original_song_id, legacy_state, original_release_date) VALUES (1, 1, 'Song', 0, '', 0, NULL, 'new', NULL)"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(live_performance_service, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_analysis, "store_setlist_summary", lambda s: None)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)
    monkeypatch.setattr(live_performance_service.gear_service, "get_band_bonus", lambda band_id, name: 0)
    monkeypatch.setattr(live_performance_service, "is_skill_blocked", lambda band_id, skill_id: False)
    monkeypatch.setattr(
        live_performance_service.chemistry_service,
        "initialize_pair",
        lambda a, b: type("P", (), {"score": 50})(),
    )

    setlist = [{"type": "song", "reference": "1"}]

    skill_service._skills.clear()
    skill_service._xp_today.clear()
    low = live_performance_service.simulate_gig(
        1, "Metro", "The Spot", setlist, reaction_stream=iter([0.5])
    )

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
    skill_service._skills[(3, perf.id)] = perf
    skill_service._skills[(3, guitar.id)] = guitar
    skill_service._skills[(4, perf.id)] = Skill(
        id=perf.id, name="performance", category="stage", xp=900, level=10
    )
    skill_service._skills[(4, drums.id)] = drums
    high = live_performance_service.simulate_gig(
        2, "Metro", "The Spot", setlist, reaction_stream=iter([0.5])
    )

    assert high["crowd_size"] > low["crowd_size"]
    assert high["fame_earned"] > low["fame_earned"]

