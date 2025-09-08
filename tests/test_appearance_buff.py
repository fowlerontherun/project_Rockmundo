import sqlite3
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from backend.models.activity import gym, running, yoga
from backend.services import lifestyle_service
from backend.models import notification_models

# Provide dummy utils modules expected by lifestyle_service
utils_mod = types.ModuleType("utils")
utils_db_mod = types.ModuleType("utils.db")
utils_db_mod.get_conn = sqlite3.connect
utils_mod.db = utils_db_mod
sys.modules["utils"] = utils_mod
sys.modules["utils.db"] = utils_db_mod


@pytest.fixture()
def setup_db(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(lifestyle_service, "DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE lifestyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            fitness REAL DEFAULT 50.0,
            appearance_score REAL DEFAULT 50.0,
            exercise_minutes REAL DEFAULT 0.0,
            last_exercise TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, fitness, appearance_score, exercise_minutes) VALUES (1, 50, 50, 0)"
    )
    conn.commit()
    conn.close()

    class DummyNotifications:
        def __init__(self):
            self.events = []

        def record_event(self, user_id, title):
            self.events.append((user_id, title))

    notifier = DummyNotifications()
    notification_models.notifications = notifier

    monkeypatch.setattr(lifestyle_service, "EXERCISE_COOLDOWN", timedelta(hours=2))

    return db_path, notifier


def fetch_appearance(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT appearance_score FROM lifestyle WHERE user_id = 1")
    val = cur.fetchone()[0]
    conn.close()
    return val


def test_appearance_buff_persistence_and_cooldown(monkeypatch, setup_db):
    db_path, notifier = setup_db

    base = datetime(2024, 1, 1, 8, 0, 0)

    class TimeMachine:
        def __init__(self, current):
            self.current = current

        def utcnow(self):
            return self.current

        @staticmethod
        def fromisoformat(val):
            return datetime.fromisoformat(val)

    tm = TimeMachine(base)
    monkeypatch.setattr(lifestyle_service, "datetime", tm)

    assert lifestyle_service.log_exercise_session(1, 30, gym.name) is True
    assert fetch_appearance(db_path) == 50 + gym.appearance_bonus

    tm.current = base + timedelta(hours=3)
    assert lifestyle_service.log_exercise_session(1, 30, running.name) is True
    assert (
        fetch_appearance(db_path)
        == 50 + gym.appearance_bonus + running.appearance_bonus
    )

    tm.current = base + timedelta(hours=6)
    assert lifestyle_service.log_exercise_session(1, 30, yoga.name) is True
    assert (
        fetch_appearance(db_path)
        == 50
        + gym.appearance_bonus
        + running.appearance_bonus
        + yoga.appearance_bonus
    )

    tm.current = base + timedelta(hours=7)
    assert lifestyle_service.log_exercise_session(1, 30, gym.name) is False
    assert (
        fetch_appearance(db_path)
        == 50
        + gym.appearance_bonus
        + running.appearance_bonus
        + yoga.appearance_bonus
    )
    assert len(notifier.events) == 3
