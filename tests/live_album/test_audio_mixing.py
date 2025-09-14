import json
import sqlite3

import pytest

from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services import audio_mixing_service
from services.live_album_service import LiveAlbumService
from services.skill_service import skill_service


def _insert_performance(cur, band_id, setlist, skill_gain, city="", venue=""):
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist, crowd_size, fame_earned,
            revenue_earned, skill_gain, merch_sold
        ) VALUES (?, ?, ?, '', ?, 0, 0, 0, ?, 0)
        """,
        (band_id, city, venue, json.dumps(setlist), skill_gain),
    )


@pytest.mark.asyncio
async def test_mixing_invoked_and_tracks_stored(tmp_path, monkeypatch):
    db_file = tmp_path / "perf.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE live_performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue TEXT,
            date TEXT,
            setlist TEXT,
            crowd_size INTEGER,
            fame_earned INTEGER,
            revenue_earned INTEGER,
            skill_gain REAL,
            merch_sold INTEGER
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE recorded_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            song_id INTEGER,
            performance_score REAL,
            created_at TEXT
        )
        """,
    )
    setlist = {
        "setlist": [
            {"type": "song", "reference": "1"},
            {"type": "song", "reference": "2"},
        ],
        "encore": [],
    }
    scores = [10, 20, 30, 40, 50]
    for idx, score in enumerate(scores, start=1):
        _insert_performance(cur, 1, setlist, 0.0, f"City {idx}", f"Venue {idx}")
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
            (idx, score),
        )
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
            (idx, score),
        )
    conn.commit()
    conn.close()

    called = {}

    def fake_mix(ids):
        called["ids"] = ids
        return [pid + 500 for pid in ids]

    monkeypatch.setattr(audio_mixing_service, "mix_tracks", fake_mix)

    service = LiveAlbumService(str(db_file))
    album = await service.compile_live_album([1, 2, 3, 4, 5], "Live")

    assert called["ids"] == [5, 5]
    assert [t["track_id"] for t in album["tracks"]] == [505, 505]
    assert all("performance_id" not in t for t in album["tracks"])


@pytest.mark.asyncio
async def test_missing_recording_raises_error(tmp_path):
    db_file = tmp_path / "perf.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE live_performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue TEXT,
            date TEXT,
            setlist TEXT,
            crowd_size INTEGER,
            fame_earned INTEGER,
            revenue_earned INTEGER,
            skill_gain REAL,
            merch_sold INTEGER
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE recorded_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            song_id INTEGER,
            performance_score REAL,
            created_at TEXT
        )
        """,
    )
    setlist = {
        "setlist": [
            {"type": "song", "reference": "1"},
            {"type": "song", "reference": "2"},
        ],
        "encore": [],
    }
    for idx in range(1, 6):
        _insert_performance(cur, 1, setlist, 0.0)
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
            (idx, 10),
        )
        if idx != 5:
            cur.execute(
                "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
                (idx, 10),
            )
    conn.commit()
    conn.close()

    service = LiveAlbumService(str(db_file))
    with pytest.raises(ValueError) as exc:
        await service.compile_live_album([1, 2, 3, 4, 5], "Live")
    assert "5" in str(exc.value)
    assert "2" in str(exc.value)


def test_mixing_awards_sound_design_xp():
    skill_service._skills.clear()
    user_id = 1
    audio_mixing_service.mix_tracks([1, 2, 3], user_id=user_id)
    skill = skill_service.train(
        user_id,
        Skill(id=SKILL_NAME_TO_ID["sound_design"], name="sound_design", category="creative"),
        0,
    )
    assert skill.xp > 0
