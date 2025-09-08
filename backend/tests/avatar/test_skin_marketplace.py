from services.avatar_service import AvatarService
from services.skin_service import SkinService, engine
from models.avatar import Avatar
from models.skin import Skin
from models.avatar_skin import AvatarSkin
from schemas.avatar import AvatarCreate
from models.avatar import Base as AvatarBase

# ensure a clean database for each test run
AvatarBase.metadata.drop_all(bind=engine)
Skin.__table__.drop(bind=engine, checkfirst=True)
Skin.__table__.create(bind=engine, checkfirst=True)
AvatarBase.metadata.create_all(bind=engine)

avatar_service = AvatarService()
skin_service = SkinService()


def _create_avatar() -> Avatar:
    avatar = avatar_service.create_avatar(
        AvatarCreate(
            character_id=1,
            nickname="Hero",
            body_type="slim",
            skin_tone="light",
            face_shape="oval",
            hair_style="short",
            hair_color="#000000",
            top_clothing="t-shirt",
            bottom_clothing="jeans",
            shoes="sneakers",
        )
    )
    return avatar


def _create_skin() -> Skin:
    with skin_service.session_factory() as session:
        skin = Skin(
            name="Cool Shirt",
            category="top_clothing",
            mesh_url="/mesh",
            texture_url="/tex",
            rarity="common",
            author="sys",
            price=100,
        )
        session.add(skin)
        session.commit()
        session.refresh(skin)
        return skin


def test_list_and_purchase_and_apply_skin():
    avatar = _create_avatar()
    skin = _create_skin()

    skins = skin_service.list_skins()
    assert any(s.id == skin.id for s in skins)

    skin_service.purchase_skin(avatar.id, skin.id)
    with skin_service.session_factory() as session:
        owned = session.query(AvatarSkin).filter_by(avatar_id=avatar.id, skin_id=skin.id).first()
        assert owned is not None
        assert owned.is_applied is False

    skin_service.apply_skin(avatar.id, skin.id)
    with skin_service.session_factory() as session:
        avatar_db = session.get(Avatar, avatar.id)
        owned = session.query(AvatarSkin).filter_by(avatar_id=avatar.id, skin_id=skin.id).first()
        assert avatar_db.top_clothing == "Cool Shirt"
        assert owned.is_applied is True

