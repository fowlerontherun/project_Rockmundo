import asyncio

import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_venue_routes import (
    create_venue,
    delete_venue,
    edit_venue,
    list_venues,
    svc as venue_svc,
)
from backend.routes.admin_business_routes import (
    create_business,
    delete_business,
    edit_business,
    list_businesses,
    svc as business_svc,
)


def test_admin_routes_require_admin():
    req = Request({})
    with pytest.raises(HTTPException):
        asyncio.run(create_venue({"owner_id": 1, "name": "A"}, req))
    with pytest.raises(HTTPException):
        asyncio.run(list_venues(req))
    with pytest.raises(HTTPException):
        asyncio.run(edit_venue(1, {"name": "B"}, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_venue(1, req))
    with pytest.raises(HTTPException):
        asyncio.run(
            create_business(
                {"owner_id": 1, "name": "B", "business_type": "shop", "location": "NY", "startup_cost": 1, "revenue_rate": 1},
                req,
            )
        )
    with pytest.raises(HTTPException):
        asyncio.run(list_businesses(req))
    with pytest.raises(HTTPException):
        asyncio.run(edit_business(1, {"name": "B"}, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_business(1, req))


def test_admin_venue_business_flow(monkeypatch):
    async def fake_current_user(req):
        return 1

    async def fake_require_role(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_venue_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_venue_routes.require_role", fake_require_role
    )
    monkeypatch.setattr(
        "backend.routes.admin_business_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_business_routes.require_role", fake_require_role
    )

    req = Request({})

    # seed economy balances
    venue_svc.economy.deposit(2, 5000)
    business_svc.economy.deposit(3, 5000)

    v = asyncio.run(
        create_venue(
            {
                "owner_id": 2,
                "name": "Arena",
                "city": "NY",
                "country": "US",
                "capacity": 1000,
                "rental_cost": 1000,
            },
            req,
        )
    )
    vid = v["id"]
    assert venue_svc.economy.get_balance(2) == 4000

    updated_v = asyncio.run(edit_venue(vid, {"capacity": 2000}, req))
    assert updated_v["capacity"] == 2000

    venues = asyncio.run(list_venues(req, owner_id=2))
    assert any(v["id"] == vid for v in venues)

    asyncio.run(delete_venue(vid, req))
    assert venue_svc.economy.get_balance(2) == 4500
    assert venue_svc.get_venue(vid) is None

    b = asyncio.run(
        create_business(
            {
                "owner_id": 3,
                "name": "Shop",
                "business_type": "merch",
                "location": "LA",
                "startup_cost": 2000,
                "revenue_rate": 500,
            },
            req,
        )
    )
    bid = b["id"]
    assert business_svc.economy.get_balance(3) == 3000

    updated_b = asyncio.run(edit_business(bid, {"location": "SF"}, req))
    assert updated_b["location"] == "SF"

    businesses = asyncio.run(list_businesses(req, owner_id=3))
    assert any(b["id"] == bid for b in businesses)

    earned = business_svc.collect_revenue(bid)
    assert earned == 500
    assert business_svc.economy.get_balance(3) == 3500

    asyncio.run(delete_business(bid, req))
    assert business_svc.economy.get_balance(3) == 4500
    assert business_svc.get_business(bid) is None
