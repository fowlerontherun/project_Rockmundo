from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import types
import sqlite3

# Stub out heavy dependencies required by auth

jwt_mod = types.ModuleType("auth.jwt")
jwt_mod.decode = lambda *args, **kwargs: {"sub": "1", "jti": "x"}
auth_mod = types.ModuleType("auth")
auth_mod.jwt = jwt_mod
sys.modules.setdefault("auth", auth_mod)
sys.modules.setdefault("auth.jwt", jwt_mod)
perm_mod = types.ModuleType("auth.permissions")
perm_mod.Permissions = object
sys.modules.setdefault("auth.permissions", perm_mod)
sys.modules.setdefault(
    "core.config",
    types.SimpleNamespace(
        settings=types.SimpleNamespace(
            auth=types.SimpleNamespace(jwt_secret="", jwt_iss="", jwt_aud="")
        )
    ),
)
sys.modules.setdefault(
    "auth.rbac",
    types.SimpleNamespace(
        rbac_service=types.SimpleNamespace(has_permission=lambda *a, **k: True)
    ),
)

class _Conn:
    def __init__(self):
        self.closed = False

    async def execute(self, *args, **kwargs):
        class _Cur:
            async def fetchone(self):
                return {"revoked_at": None}

        return _Cur()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True


_last_conn: _Conn | None = None


async def aget_conn():
    global _last_conn
    _last_conn = _Conn()
    return _last_conn


utils_mod = types.ModuleType("utils")
utils_db_mod = types.ModuleType("utils.db")
utils_db_mod.aget_conn = aget_conn
utils_db_mod.get_conn = sqlite3.connect
utils_mod.db = utils_db_mod
sys.modules["utils"] = utils_mod
sys.modules["utils.db"] = utils_db_mod

from routes import item_routes
from services.item_service import ItemService
from services.addiction_service import AddictionService
from models.item import ItemCategory
from models.drug import Drug
from services.notifications_service import NotificationsService
from models import notification_models
from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_app(tmp_path):
    db = tmp_path / "test.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
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
    item_svc = ItemService(str(db))
    addiction_svc = AddictionService(str(db))
    notification_models.notifications = NotificationsService(str(db))
    # Patch the global services used by the route
    item_routes.item_service = item_svc
    from services import item_service as item_service_module

    item_service_module.addiction_service = addiction_svc
    app = FastAPI()
    app.include_router(item_routes.router)
    app.dependency_overrides[item_routes._current_user] = lambda: 1
    return app, item_svc, addiction_svc, str(db)


def test_consume_drug(tmp_path):
    app, item_svc, addiction_svc, db = create_app(tmp_path)
    client = TestClient(app)

    item_svc.create_category(ItemCategory("drug", "Drugs"))
    drug = Drug(
        id=None,
        name="speed",
        category="drug",
        effects=["speed"],
        addiction_rate=0.5,
        duration=5,
        price_cents=0,
        stock=0,
    )
    item_svc.create_item(drug)
    item_svc.add_to_inventory(1, drug.id)

    r = client.post(f"/items/consume-drug/{drug.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["buffs"] == ["speed"]
    assert body["addiction_level"] == 10
    assert item_svc.get_inventory(1).get(drug.id, 0) == 0
    assert addiction_svc.get_level(1, "speed") == 10
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT title FROM notifications WHERE user_id = 1")
        assert cur.fetchone()[0] == "Missed show due to addiction"
