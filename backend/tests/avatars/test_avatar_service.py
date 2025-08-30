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

    fetched = svc.get_avatar(avatar.id)
    assert fetched and fetched.nickname == "Hero"

    svc.update_avatar(avatar.id, AvatarUpdate(nickname="Legend"))
    updated = svc.get_avatar(avatar.id)
    assert updated and updated.nickname == "Legend"

    assert svc.delete_avatar(avatar.id)
    assert svc.get_avatar(avatar.id) is None
