import pytest
from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase
from models.character import Character
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.learning_method import LearningMethod
from backend.models.skill import Skill
from backend.schemas.avatar import AvatarCreate, AvatarUpdate
from backend.services.avatar_service import AvatarService
from backend.services.skill_service import SkillService


def _setup_services() -> tuple[AvatarService, SkillService]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    avatar_service = AvatarService(SessionLocal)
    with SessionLocal() as session:
        c = Character(name="A", genre="rock", trait="brave", birthplace="Earth")
        session.add(c)
        session.commit()
        cid = c.id
    avatar_service.create_avatar(
        AvatarCreate(
            character_id=cid,
            nickname="A",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            stamina=50,
        )
    )
    skill_service = SkillService(avatar_service=avatar_service)
    return avatar_service, skill_service


def test_fatigue_affects_training_and_blocks():
    avatar_service, skills = _setup_services()
    skill = Skill(id=1, name="guitar", category="music")

    inst = skills.train(1, skill, 100, duration=10)
    avatar = avatar_service.get_avatar(1)
    assert avatar and avatar.fatigue == 10
    assert inst.xp == 100

    avatar_service.update_avatar(1, AvatarUpdate(fatigue=50))
    inst = skills.train(1, skill, 100)
    assert inst.xp == 150

    avatar_service.update_avatar(1, AvatarUpdate(fatigue=85))
    with pytest.raises(ValueError):
        skills.train(1, skill, 100)


def test_rest_recovers_fatigue_and_stamina():
    avatar_service, skills = _setup_services()
    skill = Skill(id=2, name="guitar", category="music")

    skills.train_with_method(1, skill, LearningMethod.PRACTICE, duration=4)
    avatar = avatar_service.get_avatar(1)
    assert avatar and avatar.fatigue == 4 and avatar.stamina < 50

    avatar_service.rest(1)
    avatar = avatar_service.get_avatar(1)
    assert avatar and avatar.fatigue == 0 and avatar.stamina == 100
