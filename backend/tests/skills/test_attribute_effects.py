from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from backend.models.skill import Skill
from backend.schemas.avatar import AvatarCreate
from backend.services.avatar_service import AvatarService
from backend.services.skill_service import SkillService


def _setup_service(attr1: dict, attr2: dict) -> AvatarService:
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
    common = dict(
        body_type="slim",
        skin_tone="pale",
        face_shape="oval",
        hair_style="short",
        hair_color="black",
        top_clothing="t",
        bottom_clothing="j",
        shoes="b",
    )
    svc.create_avatar(AvatarCreate(character_id=id1, nickname="A", **common, **attr1))
    svc.create_avatar(AvatarCreate(character_id=id2, nickname="B", **common, **attr2))
    return svc


def test_creativity_boosts_songwriting_xp():
    avatar_service = _setup_service({"creativity": 20}, {"creativity": 80})
    skills = SkillService(avatar_service=avatar_service)
    skill = Skill(id=1, name="songwriting", category="creative")
    low = skills.train(1, skill, 100)
    high = skills.train(2, skill, 100)
    assert low.xp == 110
    assert high.xp == 140


def test_discipline_reduces_decay():
    avatar_service = _setup_service({"discipline": 20}, {"discipline": 80})
    skills = SkillService(avatar_service=avatar_service)
    skill = Skill(id=2, name="guitar", category="instrument")
    # create skill entries
    skills.train(1, skill, 0)
    skills.train(2, skill, 0)
    skills._skills[(1, skill.id)].xp = 100
    skills._skills[(2, skill.id)].xp = 100
    skills.decay_skills(1, 20)
    skills.decay_skills(2, 20)
    low = skills._skills[(1, skill.id)]
    high = skills._skills[(2, skill.id)]
    assert low.xp == 82
    assert high.xp == 88
