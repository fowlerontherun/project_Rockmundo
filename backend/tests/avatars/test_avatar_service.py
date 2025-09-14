# ruff: noqa: I001
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest
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
            creativity=60,
            discipline=70,
        )
    )
    assert avatar.id is not None
    # Default mood should be neutral (50)
    assert avatar.mood == 50
    assert avatar.stamina == 50
    assert avatar.charisma == 50
    assert avatar.intelligence == 50
    assert avatar.creativity == 60
    assert avatar.discipline == 70
    assert avatar.voice == 50
    assert avatar.leadership == 0
    assert avatar.stage_presence == 50

    fetched = svc.get_avatar(avatar.id)
    assert fetched and fetched.nickname == "Hero"

    svc.update_avatar(avatar.id, AvatarUpdate(nickname="Legend", voice=80))
    updated = svc.get_avatar(avatar.id)
    assert updated and updated.nickname == "Legend" and updated.voice == 80

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


def test_update_validation_and_clamping():
    svc, SessionLocal = get_service()
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

    # Schema validation should reject out of range values
    with pytest.raises(ValueError):
        AvatarUpdate(stamina=150)
    with pytest.raises(ValueError):
        AvatarUpdate(charisma=-10)
    with pytest.raises(ValueError):
        AvatarUpdate(intelligence=101)
    with pytest.raises(ValueError):
        AvatarUpdate(creativity=120)
    with pytest.raises(ValueError):
        AvatarUpdate(discipline=-5)
    with pytest.raises(ValueError):
        AvatarUpdate(tech_savvy=200)
    with pytest.raises(ValueError):
<        AvatarUpdate(voice=150)
        AvatarUpdate(leadership=150)
    with pytest.raises(ValueError):
        AvatarUpdate(leadership=-5)
        AvatarUpdate(stage_presence=150)
    with pytest.raises(ValueError):
        AvatarUpdate(stage_presence=-10)

    # Bypass validation to ensure service clamps the values
    update_data = AvatarUpdate.model_construct(
        stamina=150,
        charisma=-10,
        intelligence=101,
        creativity=120,
        discipline=-5,
        tech_savvy=150,
        voice=150,
        leadership=150,
        stage_presence=150,
    )
    svc.update_avatar(avatar.id, update_data)
    updated = svc.get_avatar(avatar.id)
    assert (
        updated
        and updated.stamina == 100
        and updated.charisma == 0
        and updated.intelligence == 100
        and updated.creativity == 100
        and updated.discipline == 0
        and updated.tech_savvy == 100
        and updated.voice == 100
        and updated.leadership == 100
        and updated.stage_presence == 100
    )
