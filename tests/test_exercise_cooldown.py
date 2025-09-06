import sqlite3
import sys
import types
from datetime import datetime, timedelta

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
            exercise_minutes REAL DEFAULT 0.0,
            last_exercise TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, fitness, exercise_minutes) VALUES (1, 50, 0)"
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
    cur.execute("SELECT fitness FROM lifestyle WHERE user_id = 1")
    assert cur.fetchone()[0] == 50 + lifestyle_service.EXERCISE_FITNESS_BONUS
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
    cur.execute("SELECT fitness FROM lifestyle WHERE user_id = 1")
    assert cur.fetchone()[0] == 50 + lifestyle_service.EXERCISE_FITNESS_BONUS
    cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id = 1")
    assert cur.fetchone()[0] == 1
    conn.close()

