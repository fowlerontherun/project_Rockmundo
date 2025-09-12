import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from schemas.avatar import AvatarCreate
from backend.services.avatar_service import AvatarService
from backend.services import lifestyle_service


class DummySkillService:
    def reduce_burnout(self, user_id, amount=1):
        pass


def setup_services(res_low: int, res_high: int):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    avatar_svc = AvatarService(SessionLocal)

    with SessionLocal() as session:
        c1 = Character(name="L", genre="rock", trait="x", birthplace="Earth")
        c2 = Character(name="H", genre="rock", trait="x", birthplace="Earth")
        session.add_all([c1, c2])
        session.commit()
        id1, id2 = c1.id, c2.id

    av1 = avatar_svc.create_avatar(
        AvatarCreate(
            character_id=id1,
            nickname="low",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            resilience=res_low,
            stamina=50,
        )
    )
    av2 = avatar_svc.create_avatar(
        AvatarCreate(
            character_id=id2,
            nickname="high",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            resilience=res_high,
            stamina=50,
        )
    )
    return avatar_svc, av1.id, av2.id


def test_high_resilience_delays_burnout(monkeypatch):
    avatar_svc, low_id, high_id = setup_services(10, 90)
    monkeypatch.setattr(lifestyle_service, "skill_service", DummySkillService())
    lifestyle_low = {
        "user_id": low_id,
        "stress": 80,
        "drinking": "light",
        "sleep_hours": 8,
        "nutrition": 50,
        "fitness": 50,
    }
    lifestyle_high = {
        "user_id": high_id,
        "stress": 80,
        "drinking": "light",
        "sleep_hours": 8,
        "nutrition": 50,
        "fitness": 50,
    }
    lifestyle_service._RECOVERY_ACTIONS["overwork"] = {"stress": 10}
    lifestyle_service.apply_recovery_action(low_id, lifestyle_low, "overwork", avatar_service=avatar_svc)
    lifestyle_service.apply_recovery_action(high_id, lifestyle_high, "overwork", avatar_service=avatar_svc)
    assert lifestyle_low["stress"] > lifestyle_high["stress"]
    monkeypatch.setattr(random, "random", lambda: 0)
    events_low = lifestyle_service.evaluate_lifestyle_risks(lifestyle_low)
    events_high = lifestyle_service.evaluate_lifestyle_risks(lifestyle_high)
    assert "burnout" in events_low
    assert "burnout" not in events_high


def test_high_resilience_accelerates_recovery(monkeypatch):
    avatar_svc, low_id, high_id = setup_services(10, 90)
    monkeypatch.setattr(lifestyle_service, "skill_service", DummySkillService())
    lifestyle_low = {
        "user_id": low_id,
        "stress": 90,
        "drinking": "light",
        "sleep_hours": 8,
        "nutrition": 50,
        "fitness": 50,
    }
    lifestyle_high = {
        "user_id": high_id,
        "stress": 90,
        "drinking": "light",
        "sleep_hours": 8,
        "nutrition": 50,
        "fitness": 50,
    }
    lifestyle_service.apply_recovery_action(low_id, lifestyle_low, "rest", avatar_service=avatar_svc)
    lifestyle_service.apply_recovery_action(high_id, lifestyle_high, "rest", avatar_service=avatar_svc)
    assert lifestyle_high["stress"] < lifestyle_low["stress"]
    low_avatar = avatar_svc.get_avatar(low_id)
    high_avatar = avatar_svc.get_avatar(high_id)
    assert high_avatar.stamina > low_avatar.stamina
