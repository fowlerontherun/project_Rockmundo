import sqlite3
import sys
from datetime import datetime
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

from backend.models.xp_config import XPConfig, set_config  # noqa: E402
from services import scheduler_service, xp_reward_service  # noqa: E402


def _setup_db(tmp_path):
    db = tmp_path / "xp.sqlite"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            params TEXT,
            run_at TEXT,
            recurring INTEGER,
            interval_days INTEGER,
            last_run TEXT
        )
        """
    )
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
        CREATE TABLE user_levels (
            user_id INTEGER PRIMARY KEY,
            level INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    scheduler_service.DB_PATH = db
    xp_reward_service.xp_reward_service.db_path = str(db)
    set_config(XPConfig())

    return db


def test_scheduled_baseline_awards_xp(tmp_path):
    db = _setup_db(tmp_path)

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 20, 60, 70, 70, 70, datetime.utcnow().isoformat()),
    )
    cur.execute("INSERT INTO user_levels (user_id, level) VALUES (?, ?)", (1, 1))
    conn.commit()
    conn.close()

    xp_reward_service.xp_reward_service.schedule_baseline_grant(1, hours=0)
    scheduler_service.run_due_tasks()

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT amount FROM hidden_xp_rewards WHERE user_id = ?", (1,))
    row = cur.fetchone()
    conn.close()
    assert row is not None and row[0] > 0


def test_lifestyle_influences_amount(tmp_path):
    db = _setup_db(tmp_path)

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 10, 80, 90, 80, 80, datetime.utcnow().isoformat()),
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (2, 4, "none", 90, 20, 40, 30, 20, datetime.utcnow().isoformat()),
    )
    cur.executemany(
        "INSERT INTO user_levels (user_id, level) VALUES (?, ?)",
        [(1, 1), (2, 1)],
    )
    conn.commit()
    conn.close()

    xp_reward_service.xp_reward_service.schedule_baseline_grant(1, hours=0)
    xp_reward_service.xp_reward_service.schedule_baseline_grant(2, hours=0)
    scheduler_service.run_due_tasks()

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT amount FROM hidden_xp_rewards WHERE user_id = ?", (1,))
    high = cur.fetchone()[0]
    cur.execute("SELECT amount FROM hidden_xp_rewards WHERE user_id = ?", (2,))
    row = cur.fetchone()
    low = row[0] if row else 0
    conn.close()

    assert high > low


def test_baseline_respects_daily_cap(tmp_path):
    db = _setup_db(tmp_path)
    set_config(XPConfig(daily_cap=20))

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 20, 60, 70, 70, 70, datetime.utcnow().isoformat()),
    )
    cur.execute("INSERT INTO user_levels (user_id, level) VALUES (?, ?)", (1, 1))
    xp_reward_service.xp_reward_service.grant_hidden_xp(
        1, "gift", 15, conn=conn
    )
    conn.commit()
    conn.close()

    xp_reward_service.xp_reward_service.schedule_baseline_grant(1, hours=0)
    scheduler_service.run_due_tasks()

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "SELECT amount FROM hidden_xp_rewards WHERE user_id = ? ORDER BY id",
        (1,),
    )
    amounts = [row[0] for row in cur.fetchall()]
    conn.close()

    assert amounts == [15, 5]


def test_baseline_skipped_when_cap_reached(tmp_path):
    db = _setup_db(tmp_path)
    set_config(XPConfig(daily_cap=20))

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, drinking, stress, training_discipline, mental_health, nutrition, fitness, last_updated)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (1, 8, "none", 20, 60, 70, 70, 70, datetime.utcnow().isoformat()),
    )
    cur.execute("INSERT INTO user_levels (user_id, level) VALUES (?, ?)", (1, 1))
    xp_reward_service.xp_reward_service.grant_hidden_xp(
        1, "gift", 20, conn=conn
    )
    conn.commit()
    conn.close()

    xp_reward_service.xp_reward_service.schedule_baseline_grant(1, hours=0)
    scheduler_service.run_due_tasks()

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM hidden_xp_rewards WHERE user_id = ?",
        (1,),
    )
    count = cur.fetchone()[0]
    conn.close()

    assert count == 1

