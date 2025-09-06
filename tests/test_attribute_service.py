import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from backend.services.attribute_service import AttributeService  # noqa: E402


def test_attribute_levels_up():
    service = AttributeService()
    attr = service.train_attribute(user_id=1, stat="stamina", amount=150)
    assert attr.xp == 150
    assert attr.level == 2


def test_stamina_reduces_training_cost():
    service = AttributeService()
    # Train stamina to level 3 (200 xp)
    service.train_attribute(user_id=1, stat="stamina", amount=200)
    # Train strength with stamina bonus
    attr = service.train_attribute(user_id=1, stat="strength", amount=50)
    assert attr.xp == 47  # cost reduced by stamina level 3
    assert attr.level == 1
    attr = service.train_attribute(user_id=1, stat="strength", amount=60)
    # Additional 57 xp -> total 104 xp -> level 2
    assert attr.xp == 104
    assert attr.level == 2
