import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.learning_method import METHOD_PROFILES, LearningMethod
from backend.models.skill import Skill
from backend.models.tutor import Tutor
from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from backend.services.economy_service import EconomyService
from backend.services.skill_service import SkillService
from backend.services.tutor_service import TutorService
from backend.services.avatar_service import AvatarService
from schemas.avatar import AvatarCreate, AvatarUpdate


def _setup_services(tmp_path):
    db = tmp_path / "db.sqlite"
    economy = EconomyService(db_path=db)
    skills = SkillService()
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    avatar_svc = AvatarService(SessionLocal)
    svc = TutorService(economy, skills, avatar_service=avatar_svc)
    with SessionLocal() as session:
        char = Character(name="Tester", genre="rock", trait="brave", birthplace="Earth")
        session.add(char)
        session.commit()
        cid = char.id
    avatar_svc.create_avatar(
        AvatarCreate(
            character_id=cid,
            nickname="Hero",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="tshirt",
            bottom_clothing="jeans",
            shoes="boots",
            stamina=100,
        )
    )
    return svc, economy, skills, avatar_svc


def test_tutor_requires_level(tmp_path):
    svc, economy, skills, _ = _setup_services(tmp_path)
    tutor = svc.create_tutor(
        Tutor(
            id=None,
            name="Maestro",
            specialization="guitar",
            hourly_rate=70,
            level_requirement=1,
        )
    )
    skill = Skill(id=1, name="guitar", category="instrument")

    economy.deposit(1, 1000)
    balance_before = economy.get_balance(1)

    with pytest.raises(ValueError):
        svc.schedule_session(1, skill, tutor.id, 1)

    assert economy.get_balance(1) == balance_before


def test_tutor_session_cost_and_xp(tmp_path):
    svc, economy, skills, avatar_svc = _setup_services(tmp_path)
    tutor = svc.create_tutor(
        Tutor(
            id=None,
            name="Maestro",
            specialization="guitar",
            hourly_rate=70,
            level_requirement=1,
        )
    )
    skill = Skill(id=2, name="guitar", category="instrument")

    economy.deposit(1, 10000)
    # Train to level 15
    skills.train(1, skill, 1400)

    balance_before = economy.get_balance(1)

    result = svc.schedule_session(1, skill, tutor.id, 2)

    balance_after = economy.get_balance(1)
    assert balance_after == balance_before - tutor.hourly_rate * 2

    assert result["xp_per_hour"] == METHOD_PROFILES[LearningMethod.TUTOR].xp_per_hour
    assert result["xp_gained"] == METHOD_PROFILES[LearningMethod.TUTOR].xp_per_hour * 2

    # Lower stamina should increase session cost
    avatar_svc.update_avatar(1, AvatarUpdate(stamina=50))
    balance_before = economy.get_balance(1)
    svc.schedule_session(1, skill, tutor.id, 2)
    balance_after = economy.get_balance(1)
    expected_cost = tutor.hourly_rate * 2 * (200 - 50) // 100
    assert balance_after == balance_before - expected_cost
