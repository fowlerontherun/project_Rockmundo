from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models.avatar import Base, Avatar
from schemas.avatar import AvatarCreate, AvatarUpdate

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "rockmundo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)


class AvatarService:
    """Service layer providing CRUD operations for avatars."""

    def __init__(self, session_factory: Callable[[], Session] | sessionmaker = SessionLocal):
        self.session_factory = session_factory

    # ------------------------------------------------------------------
    def create_avatar(self, data: AvatarCreate) -> Avatar:
        with self.session_factory() as session:
            avatar = Avatar(**data.model_dump())
            session.add(avatar)
            session.commit()
            session.refresh(avatar)
            return avatar

    # ------------------------------------------------------------------
    def get_avatar(self, avatar_id: int) -> Optional[Avatar]:
        with self.session_factory() as session:
            return session.get(Avatar, avatar_id)

    # ------------------------------------------------------------------
    def list_avatars(self) -> list[Avatar]:
        with self.session_factory() as session:
            return session.query(Avatar).all()

    # ------------------------------------------------------------------
    def update_avatar(self, avatar_id: int, data: AvatarUpdate) -> Optional[Avatar]:
        with self.session_factory() as session:
            avatar = session.get(Avatar, avatar_id)
            if not avatar:
                return None
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(avatar, field, value)
            session.commit()
            session.refresh(avatar)
            return avatar

    # ------------------------------------------------------------------
    def delete_avatar(self, avatar_id: int) -> bool:
        with self.session_factory() as session:
            avatar = session.get(Avatar, avatar_id)
            if not avatar:
                return False
            session.delete(avatar)
            session.commit()
            return True
