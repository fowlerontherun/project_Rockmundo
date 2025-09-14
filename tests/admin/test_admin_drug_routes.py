import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import Request

BASE = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from routes.admin_drug_routes import (
    DrugCategoryIn,
    DrugIn,
    create_drug_category,
    create_drug,
    get_drug,
    svc,
)


def test_admin_drug_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "routes.admin_drug_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "routes.admin_drug_routes.require_permission", fake_require_permission
    )

    svc.db_path = str(tmp_path / "drugs.db")
    svc.ensure_schema()

    req = Request({"type": "http", "headers": []})

    cat_payload = DrugCategoryIn(name="hallucinogens", description="mind altering")
    category = asyncio.run(create_drug_category(cat_payload, req))
    assert category.name == "hallucinogens"

    drug_payload = DrugIn(
        name="Rainbow Mushrooms",
        category="hallucinogens",
        effects=["see colors"],
        addiction_rate=0.2,
        duration=60,
        price_cents=1500,
        stock=10,
    )
    drug = asyncio.run(create_drug(drug_payload, req))
    assert drug.id is not None
    assert drug.effects == ["see colors"]

    fetched = asyncio.run(get_drug(drug.id, req))
    assert fetched.effects == ["see colors"]
    assert fetched.addiction_rate == 0.2
    assert fetched.duration == 60
