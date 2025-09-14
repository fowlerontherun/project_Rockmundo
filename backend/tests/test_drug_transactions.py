from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import shop_routes
from services.item_service import ItemService
from services.city_shop_service import CityShopService
from services.loyalty_service import LoyaltyService
from services.membership_service import MembershipService
from services.shop_npc_service import ShopNPCService
from services.npc_service import NPCService
from services.economy_service import EconomyService
from models.item import ItemCategory
from models.drug import Drug


def create_app(tmp_path):
    db = tmp_path / "test.db"
    item_svc = ItemService(str(db))
    city_svc = CityShopService(str(db))
    loyalty = LoyaltyService(str(db))
    membership = MembershipService(str(db))
    economy = EconomyService(str(db))
    economy.ensure_schema()
    npc_svc = NPCService()
    npc_shop = ShopNPCService(npc_svc, city_svc, item_svc)

    shop_routes.item_service = item_svc
    shop_routes.city_shop_service = city_svc
    shop_routes.loyalty_service = loyalty
    shop_routes.membership_service = membership
    shop_routes.shop_npc_service = npc_shop
    shop_routes._economy = economy
    # ensure city shop service uses the test item service
    from services import city_shop_service as city_module

    city_module.item_service = item_svc
    city_module._economy = economy

    app = FastAPI()
    app.include_router(shop_routes.router)
    app.dependency_overrides[shop_routes._current_user] = lambda: 1
    return app, item_svc, city_svc, economy


def test_purchase_drug(tmp_path):
    app, item_svc, city_svc, economy = create_app(tmp_path)
    client = TestClient(app)

    # create category and drug item
    item_svc.create_category(ItemCategory("drug", "Drugs"))
    drug = Drug(
        id=None,
        name="Joy Pill",
        category="drug",
        effects=["happiness"],
        addiction_rate=0.6,
        duration=10,
        price_cents=100,
        stock=10,
    )
    item_svc.create_item(drug)

    # create shop and add drug
    shop = city_svc.create_shop("NYC", "Underground", owner_user_id=2)
    city_svc.add_drug(shop["id"], drug.id, quantity=5, price_cents=drug.price_cents)
    # ensure price remains stable for test
    city_svc.update_drug(shop["id"], drug.id, price_cents=drug.price_cents)

    economy.deposit(1, 1000)

    r = client.post(
        f"/shop/city/{shop['id']}/drugs/{drug.id}/purchase",
        json={"owner_user_id": 2, "quantity": 1},
    )
    assert r.status_code == 200
    assert r.json()["total_cents"] == 100
    inv = item_svc.get_inventory_item(1, drug.id)
    assert inv["quantity"] == 1
