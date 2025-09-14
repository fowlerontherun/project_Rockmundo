import sys
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Ensure the backend package is importable when tests run standalone
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

import backend.services.npc_service as npc_service_module
from services.npc_service import NPCService
from services import scheduler_service


def _setup_scheduler(tmp_path):
    db = tmp_path / "sched.sqlite"
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
    return db


def test_seasonal_event_changes_stats():
    svc = NPCService()
    npc = svc.create_npc("Bob", "villager", stats={"fame": 0, "activity": 10})
    npc_id = npc["id"]

    random.seed(0)
    svc.generate_seasonal_event(npc_id, season="summer")
    after_summer = svc.get_npc(npc_id)
    assert after_summer["stats"]["fame"] > 0

    svc.generate_seasonal_event(npc_id, season="winter")
    after_winter = svc.get_npc(npc_id)
    assert after_winter["stats"]["activity"] < 10


def test_scheduler_triggers_npc_event(tmp_path):
    _setup_scheduler(tmp_path)

    svc = NPCService()
    # Replace global references so the scheduler uses our fresh service
    npc_service_module.npc_service = svc
    scheduler_service.npc_service = svc
    scheduler_service.EVENT_HANDLERS["npc_seasonal_event"] = svc.generate_seasonal_event

    npc = svc.create_npc("Alice", "villager", stats={"fame": 0, "activity": 10})
    run_at = (datetime.utcnow() - timedelta(seconds=1)).isoformat()
    scheduler_service.schedule_npc_event(npc["id"], run_at, season="summer")

    scheduler_service.run_due_tasks()

    after = svc.get_npc(npc["id"])
    assert after["stats"]["fame"] > 0
