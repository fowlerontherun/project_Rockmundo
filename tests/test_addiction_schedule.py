import sqlite3
import types
import sys
from datetime import datetime

from services import addiction_service as global_addiction_service
from services import lifestyle_scheduler
import database

# Minimal stubs required for importing random_event_service
skill_seed = types.SimpleNamespace(SKILL_NAME_TO_ID={})
sys.modules.setdefault("seeds", types.SimpleNamespace(skill_seed=skill_seed))
sys.modules.setdefault("seeds.skill_seed", skill_seed)
discord_stub = types.SimpleNamespace(
    DiscordServiceError=Exception, send_message=lambda *args, **kwargs: None
)
sys.modules.setdefault("services", types.SimpleNamespace(discord_service=discord_stub))
sys.modules.setdefault("services.discord_service", discord_stub)
sys.modules.setdefault(
    "utils", types.SimpleNamespace(db=types.SimpleNamespace(get_conn=lambda: None))
)
sys.modules.setdefault(
    "utils.db", types.SimpleNamespace(get_conn=lambda: None)
)

import services.random_event_service as random_event_module


def test_scheduler_removes_events_on_high_addiction(tmp_path, monkeypatch):
    db_path = tmp_path / "sched.db"

    # Ensure all services use the temporary database
    monkeypatch.setattr(lifestyle_scheduler, "DB_PATH", db_path)
    monkeypatch.setattr(database, "DB_PATH", db_path)

    # Stub external dependencies not relevant for this test
    monkeypatch.setattr(
        "services.lifestyle_service.grant_daily_xp", lambda *a, **k: 0
    )
    monkeypatch.setattr(
        lifestyle_scheduler,
        "XPEventService",
        lambda: types.SimpleNamespace(get_active_multiplier=lambda: 1),
    )

    triggered = []

    def fake_trigger(user_id, level=None, date=None):
        triggered.append({"user_id": user_id, "level": level, "date": date})
        return {"type": "missed_event"}

    monkeypatch.setattr(
        random_event_module,
        "random_event_service",
        types.SimpleNamespace(trigger_addiction_event=fake_trigger),
    )

    # Prepare minimal schema and data
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE lifestyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sleep_hours REAL,
            drinking TEXT,
            stress REAL,
            training_discipline REAL,
            mental_health REAL,
            nutrition REAL,
            fitness REAL,
            last_updated TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE xp_modifiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            modifier REAL NOT NULL,
            date TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY,
            name TEXT,
            duration_hours REAL,
            category TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE daily_schedule (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            hour INTEGER,
            activity_id INTEGER,
            PRIMARY KEY (user_id, date, slot)
        )
        """
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated) VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 10, 50, 70, 50, 50, datetime.utcnow().isoformat()),
    )
    cur.execute(
        "INSERT INTO activities (id, name, duration_hours, category) VALUES (1, 'gig', 1, 'work')"
    )
    today = datetime.utcnow().date().isoformat()
    cur.execute(
        "INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id) VALUES (1, ?, 0, 0, 1)",
        (today,),
    )
    conn.commit()
    conn.close()

    # Use a fresh addiction service pointing at the temp database
    svc = global_addiction_service.AddictionService(db_path=db_path)
    monkeypatch.setattr(global_addiction_service, "addiction_service", svc)

    svc.use(1, "drug", amount=80)  # high addiction level

    lifestyle_scheduler.apply_lifestyle_decay_and_xp_effects()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM daily_schedule")
    assert cur.fetchall() == []  # schedule cleared
    conn.close()

    assert triggered and triggered[0]["user_id"] == 1
