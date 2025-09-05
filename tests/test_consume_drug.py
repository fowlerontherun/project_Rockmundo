from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import types

# Stub out heavy dependencies required by auth

fake_jwt = types.SimpleNamespace(
    decode=lambda *args, **kwargs: {"sub": "1", "jti": "x"}
)
sys.modules.setdefault("auth", types.SimpleNamespace(jwt=fake_jwt))
sys.modules.setdefault("auth.jwt", fake_jwt)
sys.modules.setdefault(
    "core.config",
    types.SimpleNamespace(
        settings=types.SimpleNamespace(
            auth=types.SimpleNamespace(jwt_secret="", jwt_iss="", jwt_aud="")
        )
    ),
)
sys.modules.setdefault(
    "services.rbac_service", types.SimpleNamespace(has_permission=lambda *a, **k: True)
)

class _Conn:
    async def execute(self, *args, **kwargs):
        class _Cur:
            async def fetchone(self):
                return {"revoked_at": None}

        return _Cur()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


async def aget_conn():
    return _Conn()


sys.modules.setdefault("utils.db", types.SimpleNamespace(aget_conn=aget_conn))

from backend.routes import item_routes
from backend.services.item_service import ItemService
from backend.services.addiction_service import AddictionService
from backend.models.item import ItemCategory
from backend.models.drug import Drug


def create_app(tmp_path):
    db = tmp_path / "test.db"
    item_svc = ItemService(str(db))
    addiction_svc = AddictionService(str(db))
    # Patch the global services used by the route
    item_routes.item_service = item_svc
    from backend.services import item_service as item_service_module

    item_service_module.addiction_service = addiction_svc
    app = FastAPI()
    app.include_router(item_routes.router)
    app.dependency_overrides[item_routes._current_user] = lambda: 1
    return app, item_svc, addiction_svc


def test_consume_drug(tmp_path):
    app, item_svc, addiction_svc = create_app(tmp_path)
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
