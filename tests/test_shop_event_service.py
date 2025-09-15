import sqlite3
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

# ensure backend module import
sys.path.append(str(Path(__file__).resolve().parents[1]))

# expose select project modules under the ``backend`` namespace for legacy imports
backend_pkg = types.ModuleType("backend")
sys.modules["backend"] = backend_pkg
sys.modules["backend.database"] = __import__("database")
sys.modules["backend.models"] = types.ModuleType("backend.models")
for _name in ("event", "event_effect", "npc", "skill"):
    sys.modules[f"backend.models.{_name}"] = __import__(
        f"models.{_name}", fromlist=[_name]
    )
sys.modules["backend.utils"] = types.ModuleType("backend.utils")
sys.modules["backend.utils.db"] = types.SimpleNamespace(
    _init_pool_async=None,
    aget_conn=None,
    cached_query=None,
    get_conn=None,
    init_pool=None,
)

fake = types.ModuleType("services.discord_service")
fake.DiscordServiceError = Exception
fake.send_message = lambda *args, **kwargs: None
sys.modules["services.discord_service"] = fake

fake_sched = types.ModuleType("services.scheduler_service")
fake_sched.schedule_task = lambda *args, **kwargs: {"status": "ok"}
sys.modules["services.scheduler_service"] = fake_sched

# stub other service dependencies not needed for shop events
sys.modules.setdefault("services.city_service", types.SimpleNamespace(city_service=None))
sys.modules.setdefault("services.npc_ai_service", types.SimpleNamespace(npc_ai_service=None))
sys.modules.setdefault("services.skill_service", types.SimpleNamespace(skill_service=None))
sys.modules.setdefault("services.weather_service", types.SimpleNamespace(weather_service=None))
sys.modules.setdefault(
    "services.reputation_service", types.SimpleNamespace(reputation_service=None)
)

fake_seed = types.ModuleType("seeds.skill_seed")
fake_seed.SKILL_NAME_TO_ID = {}
sys.modules["seeds.skill_seed"] = fake_seed

import services.event_service as event_service_module  # noqa: E402
from backend import database  # noqa: E402
from services.event_service import (  # noqa: E402
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
