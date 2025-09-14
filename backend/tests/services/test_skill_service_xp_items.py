import pytest
from models.skill import Skill
from models.xp_item import XPItem
from backend.services.skill_service import SkillService
from backend.services.xp_item_service import XPItemService


class DummyXPEvents:
    def get_active_multiplier(self, skill: str | None = None) -> float:  # pragma: no cover - simple
        return 1.0


def test_xp_items_increase_awarded_xp(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    item_db = tmp_path / "items.sqlite"
    item_svc = XPItemService(db_path=item_db)
    monkeypatch.setattr("backend.services.skill_service.xp_item_service", item_svc)

    svc = SkillService(xp_events=DummyXPEvents())
    skill = Skill(id=1, name="guitar", category="instrument")

    first = svc.train(1, skill, 10)
    baseline = first.xp
    assert baseline == 10

    item = item_svc.create_item(
        XPItem(id=None, name="double", effect_type="boost", amount=2.0, duration=60)
    )
    item_svc.assign_to_user(1, item.id)
    item_svc.apply_item(1, item.id)

    boosted = svc.train(1, skill, 10)
    assert boosted.xp - baseline == 20
