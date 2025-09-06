import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from backend.models.skill import Skill
from backend.schemas.avatar import AvatarCreate
from backend.services.avatar_service import AvatarService
from backend.services.skill_service import SkillService


def _setup_avatar_service(stamina1: int, stamina2: int) -> AvatarService:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    svc = AvatarService(SessionLocal)
    with SessionLocal() as session:
        c1 = Character(name="A", genre="rock", trait="brave", birthplace="Earth")
        c2 = Character(name="B", genre="rock", trait="calm", birthplace="Mars")
        session.add_all([c1, c2])
        session.commit()
        id1, id2 = c1.id, c2.id
    svc.create_avatar(
        AvatarCreate(
            character_id=id1,
            nickname="A",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            stamina=stamina1,
        )
    )
    svc.create_avatar(
        AvatarCreate(
            character_id=id2,
            nickname="B",
            body_type="slim",
            skin_tone="pale",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            stamina=stamina2,
        )
    )
    return svc


def test_stamina_scales_daily_decay():
    avatar_service = _setup_avatar_service(20, 80)
    skills = SkillService(avatar_service=avatar_service)
    skill = Skill(id=1, name="guitar", category="music")

    low = skills.train(1, skill, 100)
    high = skills.train(2, skill, 100)

    skills.apply_daily_decay(1, amount=10)
    skills.apply_daily_decay(2, amount=10)

    assert low.xp == 84
    assert high.xp == 90
