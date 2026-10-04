from fastapi import HTTPException

import routes.gear_routes as routes
from models.gear import GearItem


class FakeBandService:
    def get_band_info(self, band_id):
        if band_id == 7:
            return {"id": 7, "members": [{"user_id": 101}, {"user_id": 202}]}
        if band_id == 8:
            return {"id": 8, "members": [{"user_id": 303}]}
        return None


def test_gear_band_member_accepts_selected_character(monkeypatch):
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    routes._require_band_member(7, 202)


def test_gear_band_member_rejects_other_character(monkeypatch):
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    try:
        routes._require_band_member(7, 303)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("cross-character gear control was allowed")


def test_gear_owner_check_uses_actual_item_owner(monkeypatch):
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    item = GearItem(id=999, name="test", durability=100)
    routes.gear_service.items[item.id] = item
    routes.gear_service.assign_to_band(7, item)
    try:
        routes._require_item_owner_member(item.id, 303)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("another character could mutate owned gear")
    finally:
        routes.gear_service.items.pop(item.id, None)
        routes.gear_service._ownership.pop(item.id, None)
        routes.gear_service._band_items.get(7, []).remove(item.id)


def test_gear_owner_check_accepts_member_of_owner_band(monkeypatch):
    monkeypatch.setattr(routes, "_band_service", FakeBandService())
    item = GearItem(id=1000, name="test", durability=100)
    routes.gear_service.items[item.id] = item
    routes.gear_service.assign_to_band(7, item)
    try:
        assert routes._require_item_owner_member(item.id, 202) == 7
    finally:
        routes.gear_service.items.pop(item.id, None)
        routes.gear_service._ownership.pop(item.id, None)
        routes.gear_service._band_items.get(7, []).remove(item.id)
