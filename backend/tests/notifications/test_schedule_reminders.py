import importlib
import sqlite3
from datetime import datetime

from backend import database
from services import scheduler_service
from backend.models import notification_models
from services.notifications_service import NotificationsService


DDL = """
CREATE TABLE scheduled_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    params TEXT,
    run_at TEXT,
    recurring INTEGER,
    interval_days INTEGER,
    last_run TEXT
);
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    read_at TEXT
);
CREATE TABLE daily_schedule (
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    slot INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    PRIMARY KEY(user_id, date, slot)
);
CREATE TABLE activity_log (
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    activity_id INTEGER NOT NULL,
    outcome_json TEXT
);
"""


def _setup(tmp_path):
    db = tmp_path / "reminders.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(DDL)

    # Point services at the temp database
    database.DB_PATH = db
    importlib.reload(scheduler_service)
    importlib.reload(notification_models)
    notification_models.notifications = NotificationsService(db_path=str(db))
    return str(db)


def _count_notifications(db):
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM notifications")
        return cur.fetchone()[0]


def test_plan_reminder_sends_when_no_plan(tmp_path):
    db = _setup(tmp_path)
    day = "2024-01-01"
    scheduler_service.schedule_plan_reminder(1, day, datetime.utcnow().isoformat())
    scheduler_service.run_due_tasks()
    assert _count_notifications(db) == 1


def test_plan_reminder_skips_when_plan_exists(tmp_path):
    db = _setup(tmp_path)
    day = "2024-01-02"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id) VALUES (1, ?, 0, 0, 1)",
            (day,),
        )
    scheduler_service.schedule_plan_reminder(1, day, datetime.utcnow().isoformat())
    scheduler_service.run_due_tasks()
    assert _count_notifications(db) == 0


def test_outcome_reminder_sends_when_unprocessed(tmp_path):
    db = _setup(tmp_path)
    day = "2024-01-03"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id) VALUES (1, ?, 0, 0, 1)",
            (day,),
        )
    scheduler_service.schedule_outcome_reminder(1, day, datetime.utcnow().isoformat())
    scheduler_service.run_due_tasks()
    assert _count_notifications(db) == 1


def test_outcome_reminder_skips_when_processed(tmp_path):
    db = _setup(tmp_path)
    day = "2024-01-04"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id) VALUES (1, ?, 0, 0, 1)",
            (day,),
        )
        conn.execute(
            "INSERT INTO activity_log (user_id, date, activity_id, outcome_json) VALUES (1, ?, 1, '{}')",
            (day,),
        )
    scheduler_service.schedule_outcome_reminder(1, day, datetime.utcnow().isoformat())
    scheduler_service.run_due_tasks()
    assert _count_notifications(db) == 0

