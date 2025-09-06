import sqlite3

from backend.services import fan_service
from backend.services.business_service import BusinessService
from backend.services.business_training_service import BusinessTrainingService
from backend.services.skill_service import skill_service


def test_business_training_awards_xp(tmp_path):
    skill_service.db_path = tmp_path / "skills.db"
    skill_service._skills.clear()
    svc = BusinessTrainingService(skill_service=skill_service)

    marketing = svc.attend_workshop(1, "marketing")
    assert marketing.xp == 50
    assert marketing.level == 1

    finance = svc.attend_course(1, "financial_management")
    assert finance.xp == 120
    assert finance.level == 2


def test_marketing_pr_boost_fans(tmp_path, monkeypatch):
    db = tmp_path / "fans.db"
    monkeypatch.setattr(fan_service, "DB_PATH", db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE fans (user_id INTEGER, band_id INTEGER, location TEXT, loyalty INTEGER, source TEXT)"
        )
        conn.commit()

    skill_service.db_path = tmp_path / "skills.db"
    skill_service._skills.clear()
    training = BusinessTrainingService(skill_service=skill_service)

    # baseline
    result = fan_service.boost_fans_after_gig(1, "NY", 100)
    assert result["fans_boosted"] == 10

    # train skills to level 3 each (200 XP)
    for _ in range(4):
        training.attend_workshop(1, "marketing")
        training.attend_workshop(1, "public_relations")

    result = fan_service.boost_fans_after_gig(1, "NY", 100)
    assert result["fans_boosted"] == 12


def test_financial_management_boosts_revenue(tmp_path):
    class DummyEconomy:
        def __init__(self):
            self.deposits: list[tuple[int, int]] = []

        def deposit(self, user_id: int, amount_cents: int) -> None:
            self.deposits.append((user_id, amount_cents))

        def withdraw(self, user_id: int, amount_cents: int) -> None:  # pragma: no cover - not used
            pass

        def ensure_schema(self) -> None:  # pragma: no cover - not used
            pass

    db = tmp_path / "biz.db"
    eco = DummyEconomy()
    svc = BusinessService(db_path=str(db), economy=eco)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO businesses (id, owner_id, name, business_type, location, startup_cost, revenue_rate)"
            " VALUES (1, 1, 'biz', 'type', 'loc', 0, 100)"
        )
        conn.commit()

    skill_service.db_path = tmp_path / "skills.db"
    skill_service._skills.clear()

    amount = svc.collect_revenue(1)
    assert amount == 100
    assert eco.deposits[-1] == (1, 100)

    training = BusinessTrainingService(skill_service=skill_service)
    training.attend_course(1, "financial_management")
    training.attend_course(1, "financial_management")

    amount = svc.collect_revenue(1)
    assert amount == 110
    assert eco.deposits[-1] == (1, 110)
