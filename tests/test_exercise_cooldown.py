import sqlite3
import sys
import types
from datetime import datetime, timedelta

import pytest
from backend.models.activity import gym, running, yoga

utils_mod = types.ModuleType("utils")
utils_db_mod = types.ModuleType("utils.db")
utils_db_mod.get_conn = sqlite3.connect
utils_mod.db = utils_db_mod
sys.modules["utils"] = utils_mod
sys.modules["utils.db"] = utils_db_mod

from backend.services import lifestyle_service
from backend.services.notifications_service import NotificationsService
from backend.models import notification_models


def test_exercise_cooldown(monkeypatch, tmp_path):
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
    cur.execute(
        """
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            read_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    notification_models.notifications = NotificationsService(str(db_path))

    base = datetime(2024, 1, 1, 8, 0, 0)

    class T1:
        @staticmethod
        def utcnow():
            return base

        @staticmethod
        def fromisoformat(val):
            return datetime.fromisoformat(val)

    monkeypatch.setattr(lifestyle_service, "datetime", T1)
    assert lifestyle_service.log_exercise_session(1, 30) is True

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT fitness, appearance_score FROM lifestyle WHERE user_id = 1")
    fitness, appearance = cur.fetchone()
    assert fitness == 50 + lifestyle_service.EXERCISE_FITNESS_BONUS
    assert appearance == 50 + gym.appearance_bonus
    cur.execute("SELECT title FROM notifications WHERE user_id = 1")
    assert cur.fetchone()[0] == "Appearance buff gained"
    conn.close()

    class T2:
        @staticmethod
        def utcnow():
            return base + timedelta(hours=2)

        @staticmethod
        def fromisoformat(val):
            return datetime.fromisoformat(val)

    monkeypatch.setattr(lifestyle_service, "datetime", T2)
    assert lifestyle_service.log_exercise_session(1, 30) is False

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT fitness, appearance_score FROM lifestyle WHERE user_id = 1")
    fitness, appearance = cur.fetchone()
    assert fitness == 50 + lifestyle_service.EXERCISE_FITNESS_BONUS
    assert appearance == 50 + gym.appearance_bonus
    cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = 1")
    assert cur.fetchone()[0] == 1
    conn.close()


@pytest.mark.parametrize(
    "activity_obj",
    [gym, running, yoga],
)
def test_appearance_bonus(monkeypatch, tmp_path, activity_obj):
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

    base = datetime(2024, 1, 1, 8, 0, 0)

    class T:
        @staticmethod
        def utcnow():
            return base

        @staticmethod
        def fromisoformat(val):
            return datetime.fromisoformat(val)

    monkeypatch.setattr(lifestyle_service, "datetime", T)
    assert lifestyle_service.log_exercise_session(1, 30, activity_obj.name) is True

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT appearance_score FROM lifestyle WHERE user_id = 1")
    assert cur.fetchone()[0] == 50 + activity_obj.appearance_bonus
    conn.close()
    assert notifier.events == [(1, "Appearance buff gained")]

