# ruff: noqa: I001
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from schemas.avatar import AvatarCreate, AvatarUpdate
from services.avatar_service import AvatarService


def get_service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    svc = AvatarService(SessionLocal)
    return svc, SessionLocal


def test_crud_lifecycle():
    svc, SessionLocal = get_service()
    # create a character to satisfy FK
    with SessionLocal() as session:
        char = Character(name="Tester", genre="rock", trait="brave", birthplace="Earth")
        session.add(char)
        session.commit()
        cid = char.id

    avatar = svc.create_avatar(
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
        )
    )
    assert avatar.id is not None
    # Default mood should be neutral (50)
    assert avatar.mood == 50
    assert avatar.stamina == 50
    assert avatar.charisma == 50
    assert avatar.intelligence == 50

    fetched = svc.get_avatar(avatar.id)
    assert fetched and fetched.nickname == "Hero"

    svc.update_avatar(avatar.id, AvatarUpdate(nickname="Legend"))
    updated = svc.get_avatar(avatar.id)
    assert updated and updated.nickname == "Legend"

    # Adjust mood based on lifestyle and events
    updated = svc.adjust_mood(avatar.id, lifestyle_score=80, events=["burnout"])
    assert updated and updated.mood == 55
    # get_mood should reflect persisted value
    assert svc.get_mood(avatar.id) == 55

    # Stamina recovery should increase stamina but not exceed 100
    svc.update_avatar(avatar.id, AvatarUpdate(stamina=40))
    svc.recover_stamina(avatar.id, 15)
    recovered = svc.get_avatar(avatar.id)
    assert recovered and recovered.stamina == 55

    assert svc.delete_avatar(avatar.id)
    assert svc.get_avatar(avatar.id) is None
