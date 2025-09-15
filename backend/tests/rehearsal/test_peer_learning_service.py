import sqlite3
from datetime import datetime

from backend.services import scheduler_service
from backend.services.rehearsal_service import RehearsalService
from backend.services.peer_learning_service import peer_learning_service
from backend.services.skill_service import skill_service
from seeds.skill_seed import SKILL_NAME_TO_ID


def _setup(tmp_path):
    db = tmp_path / "peer.sqlite"
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
    conn.commit()
    conn.close()

    scheduler_service.DB_PATH = db
    peer_learning_service.db_path = db
    skill_service.db_path = db
    skill_service._skills.clear()
    skill_service._xp_today.clear()

    svc = RehearsalService(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO bands (id, name, cohesion) VALUES (1, 'Band', 2)"
        )
    return svc, db


def test_peer_learning_xp(tmp_path):
    svc, db = _setup(tmp_path)

    start = "2024-01-01T10:00:00"
    end = "2024-01-01T11:00:00"
    svc.book_session(1, start, end, [1, 2, 3])

    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT event_type FROM scheduled_tasks"
        ).fetchall()
    assert rows == [("peer_learning",)]

    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE scheduled_tasks SET run_at = ?",
            (datetime.utcnow().isoformat(),),
        )
        conn.commit()

    scheduler_service.run_due_tasks()

    perf_id = SKILL_NAME_TO_ID["performance"]
    xp_values = [skill_service._skills[(uid, perf_id)].xp for uid in [1, 2, 3]]
    assert xp_values == [2, 2, 2]
