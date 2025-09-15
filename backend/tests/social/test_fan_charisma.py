import asyncio
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from schemas.avatar import AvatarCreate
from backend.services.avatar_service import AvatarService
from backend.services.fan_club_service import FanClubService


@pytest.fixture
def avatar_service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    svc = AvatarService(SessionLocal)
    with SessionLocal() as session:
        char = Character(name="Hero", genre="rock", trait="bold", birthplace="Earth")
        session.add(char)
        session.commit()
        cid = char.id
    svc.create_avatar(
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
            charisma=80,
        )
    )
    return svc


def test_charisma_increases_post_engagement(avatar_service, monkeypatch):
    async def fake_publish(*args, **kwargs):
        return 0

    monkeypatch.setattr(
        "backend.services.fan_club_service.publish_fan_club_post", fake_publish
    )

    fan_svc = FanClubService(avatar_service=avatar_service)
    club = fan_svc.create_club(owner_id=1, name="Fans")
    fan_svc.join_club(club.id, 1)
    thread = fan_svc.create_thread(club.id, 1, "Welcome")
    post = asyncio.get_event_loop().run_until_complete(
        fan_svc.add_post(thread.id, author_id=1, content="Hi")
    )
    assert post.engagement == 8
