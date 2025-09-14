import json
import sqlite3

from services import live_performance_service, live_performance_analysis, setlist_service
from services.city_service import city_service
from backend.models.city import City


def test_crowd_reaction_adjusts_and_logs(monkeypatch, tmp_path):
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
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)")
    cur.execute(
        "CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)"
    )
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER, legacy_state TEXT DEFAULT 'new', original_release_date TEXT)"
    )
    cur.execute(
        "CREATE TABLE performance_events (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, action TEXT, crowd_reaction REAL, fame_modifier INTEGER, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE setlist_summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, performance_id INTEGER, summary TEXT, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE band_members (band_id INTEGER, user_id INTEGER)"
    )
    cur.execute(
        "CREATE TABLE setlist_revisions (id INTEGER PRIMARY KEY AUTOINCREMENT, setlist_id INTEGER NOT NULL, setlist TEXT NOT NULL, author TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, approved INTEGER DEFAULT 0)"
    )
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (1, 100, 0, 0)")
    cur.executemany(
        "INSERT INTO band_members (band_id, user_id) VALUES (?, ?)",
        [(1, 1), (1, 2)],
    )
    cur.execute(
        "INSERT INTO songs (id, band_id, title, duration_sec, genre, play_count, original_song_id, legacy_state) VALUES (1, 1, 'Song A', 0, '', 0, NULL, 'new')"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(live_performance_service, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_analysis, "DB_PATH", db_file)
    monkeypatch.setattr(setlist_service, "DB_PATH", db_file)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)
    monkeypatch.setattr(live_performance_service.gear_service, "get_band_bonus", lambda band_id, name: 0)
    monkeypatch.setattr(live_performance_service, "is_skill_blocked", lambda band_id, skill_id: False)
    monkeypatch.setattr(
        live_performance_service.chemistry_service,
        "initialize_pair",
        lambda a, b: type("P", (), {"score": 90})(),
    )

    setlist = [
        {"type": "song", "reference": "1"},
        {"type": "song", "reference": "1"},
    ]
    revision_id = setlist_service.create_revision(1, setlist, "tester")
    setlist_service.approve_revision(1, revision_id)


    reaction = iter([0.9, 0.9])
    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", revision_id, reaction_stream=reaction)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("UPDATE bands SET fame = 100 WHERE id = 1")
    cur.execute("DELETE FROM performance_events")
    conn.commit()
    conn.close()

    reaction = iter([
        {"cheers": 0.9, "energy": 0.9},
        {"cheers": 0.9, "energy": 0.9},
    ])
    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", setlist, reaction_stream=reaction)


    assert result["fame_earned"] == 27

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT action, crowd_reaction, fame_modifier FROM performance_events ORDER BY id")
    rows = cur.fetchall()
    assert rows == [("song", 1.0, 0), ("song", 1.0, 1)]
    cur.execute("SELECT summary FROM setlist_summaries")
    summary = json.loads(cur.fetchone()[0])
    assert summary["average_reaction"] == 1.0
    assert summary["actions"][0]["cheers"] == 0.9
    conn.close()

