from __future__ import annotations

from typing import Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.avatar import Avatar, Base as AvatarBase
from models.skin import Skin
from models.avatar_skin import AvatarSkin
from schemas.skin import SkinCreate, SkinUpdate

# Reuse the same SQLite database as AvatarService
from services.avatar_service import DB_PATH

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Ensure tables exist
Skin.__table__.create(bind=engine, checkfirst=True)
AvatarBase.metadata.create_all(bind=engine)


class SkinService:
    """Marketplace operations for avatar skins."""

    def __init__(self, session_factory: Callable[[], Session] | sessionmaker = SessionLocal):
        self.session_factory = session_factory

    # ------------------------------------------------------------------
    def list_skins(self) -> list[Skin]:
        with self.session_factory() as session:
            return session.query(Skin).all()

    # ------------------------------------------------------------------
    def get_skin(self, skin_id: int) -> Optional[Skin]:
        """Retrieve a single skin by ID."""

        with self.session_factory() as session:
            return session.get(Skin, skin_id)

    # ------------------------------------------------------------------
    def create_skin(self, data: SkinCreate) -> Skin:
        """Create a new skin in the marketplace."""

        with self.session_factory() as session:
            skin = Skin(**data.model_dump())
            session.add(skin)
            session.commit()
            session.refresh(skin)
            return skin

    # ------------------------------------------------------------------
    def update_skin(self, skin_id: int, data: SkinUpdate) -> Optional[Skin]:
        """Update an existing skin and return the updated row."""

        with self.session_factory() as session:
            skin = session.get(Skin, skin_id)
            if not skin:
                return None
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(skin, field, value)
            session.commit()
            session.refresh(skin)
            return skin

    # ------------------------------------------------------------------
    def delete_skin(self, skin_id: int) -> bool:
        """Delete a skin.  Returns ``True`` if the skin existed."""

        with self.session_factory() as session:
            skin = session.get(Skin, skin_id)
            if not skin:
                return False
            session.delete(skin)
            session.commit()
            return True

    # ------------------------------------------------------------------
    def purchase_skin(self, avatar_id: int, skin_id: int) -> AvatarSkin:
        with self.session_factory() as session:
            owned = (
                session.query(AvatarSkin)
                .filter_by(avatar_id=avatar_id, skin_id=skin_id)
                .first()
            )
            if owned:
                return owned
            avatar_skin = AvatarSkin(avatar_id=avatar_id, skin_id=skin_id)
            session.add(avatar_skin)
            session.commit()
            session.refresh(avatar_skin)
            return avatar_skin

    # ------------------------------------------------------------------
    def apply_skin(self, avatar_id: int, skin_id: int) -> Optional[Avatar]:
        with self.session_factory() as session:
            avatar_skin = (
                session.query(AvatarSkin)
                .filter_by(avatar_id=avatar_id, skin_id=skin_id)
                .first()
            )
            if not avatar_skin:
                return None
            skin = session.get(Skin, skin_id)
            avatar = session.get(Avatar, avatar_id)
            if not skin or not avatar:
                return None
            # Reset other skins for this avatar
            session.query(AvatarSkin).filter_by(avatar_id=avatar_id).update({"is_applied": False})
            avatar_skin.is_applied = True
            # Apply appearance based on category
            try:
                setattr(avatar, skin.category, skin.name)
            except Exception:
                pass
            session.commit()
            session.refresh(avatar)
            return avatar
