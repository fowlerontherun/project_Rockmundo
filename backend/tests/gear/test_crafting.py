from services.gear_service import GearService
from backend.models.gear import BaseItem, GearComponent, StatModifier


def test_crafting_success(monkeypatch):
    svc = GearService()
    svc.base_items["amp"] = BaseItem(name="amp", durability=50)
    svc.components["tube"] = GearComponent(
        name="tube",
        success_rate=0.8,
        durability_bonus=5,
        modifiers=[StatModifier("performance", 1.0)],
    )

    monkeypatch.setattr("backend.services.gear_service.random.random", lambda: 0.1)
    item = svc.craft("amp", ["tube"])
    assert item is not None
    assert item.durability == 55
    assert item.modifiers[0].stat == "performance"


def test_crafting_failure(monkeypatch):
    svc = GearService()
    svc.base_items["amp"] = BaseItem(name="amp", durability=50)
    svc.components["tube"] = GearComponent(name="tube", success_rate=0.2)

    monkeypatch.setattr("backend.services.gear_service.random.random", lambda: 0.9)
    item = svc.craft("amp", ["tube"])
    assert item is None
