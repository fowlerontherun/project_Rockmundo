import sqlite3

from backend.services import live_performance_service
from backend.services import live_performance_analysis
from backend.services.city_service import city_service
from backend.models.city import City


def test_simulate_gig_parses_structured_setlist(monkeypatch, tmp_path):
    city_service.cities.clear()
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={}, event_modifier=1.0, market_index=1.0))

    db_file = tmp_path / "gig.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)")
    cur.execute(
        "CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)"
    )
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER)"
    )
    cur.execute(
        "CREATE TABLE performance_events (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, action TEXT, crowd_reaction REAL, fame_modifier INTEGER, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE setlist_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, summary TEXT, created_at TEXT)"
    )
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (1, 100, 0, 0)")
    cur.executemany(
        "INSERT INTO songs (id, band_id, title, duration_sec, genre, play_count, original_song_id) VALUES (?, ?, ?, 0, '', 0, NULL)",
        [
            (1, 1, 'Song A'),
            (2, 1, 'Song B'),
        ],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(live_performance_service, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_analysis, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)
    monkeypatch.setattr(live_performance_service.gear_service, "get_band_bonus", lambda band_id, name: 0)
    monkeypatch.setattr(live_performance_service, "is_skill_blocked", lambda band_id, skill_id: False)

    setlist = [
        {"type": "song", "reference": "1"},
        {"type": "activity", "description": "banter"},
        {"type": "song", "reference": "2", "encore": True},
    ]

    reaction = iter([0.5, 0.5, 0.5])
    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", setlist, reaction_stream=reaction)

    assert result["fame_earned"] == 28
    assert result["skill_gain"] == 0.7


def test_cover_song_reduces_fame_and_boosts_original(monkeypatch, tmp_path):
    city_service.cities.clear()
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={}, event_modifier=1.0, market_index=1.0))

    db_file = tmp_path / "gig.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)")
    cur.execute(
        "CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)"
    )
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER)"
    )
    cur.execute(
        "CREATE TABLE performance_events (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, action TEXT, crowd_reaction REAL, fame_modifier INTEGER, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE setlist_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, summary TEXT, created_at TEXT)"
    )
    cur.executemany(
        "INSERT INTO bands (id, fame, skill, revenue) VALUES (?, ?, 0, 0)",
        [(1, 100), (2, 50)],
    )
    cur.executemany(
        "INSERT INTO songs (id, band_id, title, duration_sec, genre, play_count, original_song_id) VALUES (?, ?, ?, 0, '', 0, NULL)",
        [
            (1, 1, 'Song A'),
            (2, 2, 'Song B'),
        ],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(live_performance_service, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_analysis, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)
    monkeypatch.setattr(live_performance_service.gear_service, "get_band_bonus", lambda band_id, name: 0)
    monkeypatch.setattr(live_performance_service, "is_skill_blocked", lambda band_id, skill_id: False)

    setlist = [
        {"type": "song", "reference": "1"},  # own song
        {"type": "song", "reference": "2"},  # cover
    ]

    reaction = iter([0.5, 0.5])
    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", setlist, reaction_stream=reaction)

    assert result["fame_earned"] == 23
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT play_count FROM songs WHERE id = 1")
    assert cur.fetchone()[0] == 2
    cur.execute("SELECT play_count FROM songs WHERE id = 2")
    assert cur.fetchone()[0] == 1
    conn.close()
