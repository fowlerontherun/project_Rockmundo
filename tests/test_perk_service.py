import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

from models.perk import Perk
from models.skill import Skill
from backend.services.attribute_service import AttributeService
from backend.services.perk_service import perk_service
from backend.services.skill_service import SkillService


def setup_function() -> None:
    perk_service.reset()


def test_perk_unlocks_from_attribute() -> None:
    perk_service.register_perk(
        Perk(id=1, name="Muscle", description="Be strong", requirements={"strength": 2})
    )
    attrs = AttributeService()
    attrs.train_attribute(1, "strength", 101)
    perks = perk_service.get_perks(1)
    assert len(perks) == 1 and perks[0].name == "Muscle"
    # Further training of other stats should not remove the perk
    attrs.train_attribute(1, "stamina", 50)
    perks = perk_service.get_perks(1)
    assert len(perks) == 1


def test_perk_unlocks_from_skill() -> None:
    perk_service.register_perk(
        Perk(id=2, name="Guitar Hero", description="Skill perk", requirements={"guitar": 2})
    )
    svc = SkillService()
    skill = Skill(id=99, name="guitar", category="instrument")
    svc.train(1, skill, 100)
    perks = perk_service.get_perks(1)
    assert len(perks) == 1 and perks[0].name == "Guitar Hero"
    # Training other skills should keep the perk unlocked
    other = Skill(id=100, name="drums", category="instrument")
    svc.train(1, other, 50)
    perks = perk_service.get_perks(1)
    assert any(p.name == "Guitar Hero" for p in perks)
