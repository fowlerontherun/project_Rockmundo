import sqlite3
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

# ensure backend module import
sys.path.append(str(Path(__file__).resolve().parents[1]))

fake = types.ModuleType("services.discord_service")
fake.DiscordServiceError = Exception
fake.send_message = lambda *args, **kwargs: None
sys.modules["services.discord_service"] = fake

fake_sched = types.ModuleType("backend.services.scheduler_service")
fake_sched.schedule_task = lambda *args, **kwargs: {"status": "ok"}
sys.modules["backend.services.scheduler_service"] = fake_sched

fake_seed = types.ModuleType("seeds.skill_seed")
fake_seed.SKILL_NAME_TO_ID = {}
sys.modules["seeds.skill_seed"] = fake_seed

import backend.services.event_service as event_service_module  # noqa: E402
from backend import database  # noqa: E402
from backend.services.event_service import (  # noqa: E402
    end_shop_event,
    schedule_shop_event,
    start_shop_event,
)


def _setup_db(tmp_path):
    db = tmp_path / "shop.sqlite"
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
        CREATE TABLE shop_items (
            shop_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            price_cents INTEGER
        )
        """
    )
    cur.execute(
        "INSERT INTO shop_items (shop_id, item_id, quantity, price_cents) VALUES (1,1,10,100)"
    )
    conn.commit()
    conn.close()
    database.DB_PATH = db
    event_service_module.DB_PATH = db
    return db


def test_shop_event_modifies_inventory_and_price(tmp_path):
    _setup_db(tmp_path)
    start = datetime.utcnow().isoformat()
    end = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    data = {
        "name": "Sale",
        "banner": "Half off!",
        "shop_id": 1,
        "start_time": start,
        "end_time": end,
        "inventory": {1: 5},
        "price_modifier": 0.5,
    }
    res = schedule_shop_event(data)
    event_id = res["event_id"]
    start_shop_event(event_id)

    conn = sqlite3.connect(database.DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT quantity, price_cents FROM shop_items WHERE shop_id=1 AND item_id=1")
    qty, price = cur.fetchone()
    assert qty == 15
    assert price == 50

    end_shop_event(event_id)
    cur.execute("SELECT price_cents FROM shop_items WHERE shop_id=1 AND item_id=1")
    price2 = cur.fetchone()[0]
    assert price2 == 100
    conn.close()
