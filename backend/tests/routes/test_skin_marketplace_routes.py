from fastapi import FastAPI
import base64
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.storage.local import LocalStorage
from services.skin_service import SkinService, engine
from models.skin import Skin
from models.avatar import Base as AvatarBase
from services.payment_service import PaymentService, MockGateway
from services.economy_service import EconomyService
from routes import skin_marketplace


def create_app(tmp_path):
    # reset DB tables
    AvatarBase.metadata.drop_all(bind=engine)
    Skin.__table__.drop(bind=engine, checkfirst=True)
    Skin.__table__.create(bind=engine, checkfirst=True)
    AvatarBase.metadata.create_all(bind=engine)

    svc = SkinService()
    skin_marketplace.svc = svc

    econ_db = tmp_path / "econ.db"
    economy = EconomyService(str(econ_db))
    economy.ensure_schema()
    gateway = MockGateway(prefix="test")
    payments = PaymentService(gateway, economy)
    skin_marketplace.payments = payments

    storage_root = tmp_path / "storage"
    storage = LocalStorage(root=str(storage_root), public_base_url="http://test")
    skin_marketplace.get_storage_backend = lambda: storage

    app = FastAPI()
    app.include_router(skin_marketplace.router)
    return app, gateway


def test_upload_list_purchase_flow(tmp_path):
    app, gateway = create_app(tmp_path)
    client = TestClient(app)

    mesh_b64 = base64.b64encode(b"meshdata").decode()
    tex_b64 = base64.b64encode(b"texdata").decode()
    data = {
        "name": "Cool Shirt",
        "category": "top_clothing",
        "rarity": "common",
        "author": "sys",
        "price": 100,
        "mesh_b64": mesh_b64,
        "texture_b64": tex_b64,
    }
    r = client.post("/skins/upload", json=data)
    assert r.status_code == 200
    skin_id = r.json()["id"]

    r = client.get("/skins/")
    assert r.status_code == 200
    assert any(s["id"] == skin_id for s in r.json())

    r = client.post(f"/skins/{skin_id}/purchase", json={"avatar_id": 1})
    assert r.status_code == 200
    assert r.json()["status"] == "purchased"
    assert gateway.counter == 1
