from __future__ import annotations  # noqa: I001

from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import NoReferencedTableError
from sqlalchemy.orm import Session, sessionmaker

from models.avatar import Avatar, Base
from schemas.avatar import AvatarCreate, AvatarUpdate
try:  # pragma: no cover - optional when character model unavailable
    from models.character import Base as CharacterBase  # type: ignore
except Exception:  # pragma: no cover
    CharacterBase = None  # type: ignore

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "rockmundo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure the parent directory exists so SQLite can create the DB file without
# raising an OperationalError during imports or test initialisation.
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
if CharacterBase is not None:
    CharacterBase.metadata.create_all(bind=engine)
try:  # pragma: no cover - character table may be created elsewhere
    Base.metadata.create_all(bind=engine)
except NoReferencedTableError:  # pragma: no cover
    pass


class AvatarService:
    """Service layer providing CRUD operations for avatars."""

    def __init__(self, session_factory: Callable[[], Session] | sessionmaker = SessionLocal):
        self.session_factory = session_factory

    # ------------------------------------------------------------------
    def create_avatar(self, data: AvatarCreate) -> Avatar:
        with self.session_factory() as session:
            payload = data.model_dump()
            payload.setdefault("luck", 0)
            payload.setdefault("social_media", 0)
            payload.setdefault("tech_savvy", 0)
            payload.setdefault("networking", 0)
            payload.setdefault("leadership", 0)
            payload.setdefault("stage_presence", 50)
            payload.setdefault("resilience", 50)
            payload.setdefault("voice", 50)
            payload.setdefault("fatigue", 0)
            avatar = Avatar(**payload)
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
                if field in {
                    "stamina",
                    "fatigue",
                    "charisma",
                    "intelligence",
                    "creativity",
                    "discipline",
                    "resilience",
                    "voice",
                    "luck",
                    "social_media",
                    "tech_savvy",
                    "networking",
                    "leadership",
                    "stage_presence",
                } and value is not None:
                    setattr(avatar, field, max(0, min(100, value)))
                else:
                    setattr(avatar, field, value)
            session.commit()
            session.refresh(avatar)
            return avatar

    # ------------------------------------------------------------------
    def rest(self, avatar_id: int) -> Optional[Avatar]:
        """Fully restore stamina and clear fatigue."""

        with self.session_factory() as session:
            avatar = session.get(Avatar, avatar_id)
            if not avatar:
                return None
            avatar.stamina = 100
            avatar.fatigue = 0
            session.commit()
            session.refresh(avatar)
            return avatar

    # ------------------------------------------------------------------
    def get_avatar_by_character_id(self, character_id: int) -> Optional[Avatar]:
        with self.session_factory() as session:
            return (
                session.query(Avatar)
                .filter(Avatar.character_id == character_id)
                .first()
            )

    # ------------------------------------------------------------------
    def recover_stamina(self, avatar_id: int, amount: int) -> Optional[Avatar]:
        """Increase an avatar's stamina by ``amount`` up to a maximum of 100."""

        with self.session_factory() as session:
            avatar = session.get(Avatar, avatar_id)
            if not avatar:
                return None
            avatar.stamina = min(100, avatar.stamina + amount)
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

    # ------------------------------------------------------------------
    def adjust_mood(
        self,
        avatar_id: int,
        lifestyle_score: float,
        events: list[str] | None = None,
    ) -> Optional[Avatar]:
        """Adjust an avatar's mood.

        ``lifestyle_score`` is expected to be a 0-100 value summarising the
        avatar's wellbeing.  Mood will drift toward this score.  Any events
        passed in can further modify the result.  The mood value is clamped
        to the 0-100 range before persisting.
        """

        events = events or []
        with self.session_factory() as session:
            avatar = session.get(Avatar, avatar_id)
            if not avatar:
                return None
            # Move mood halfway toward lifestyle score for gentle adjustments.
            avatar.mood = int((avatar.mood + lifestyle_score) / 2)
            # Negative events impact mood further.
            if "burnout" in events:
                avatar.mood -= 10
            if "illness" in events:
                avatar.mood -= 5
            if "mental fatigue" in events:
                avatar.mood -= 3
            avatar.mood = max(0, min(100, avatar.mood))
            session.commit()
            session.refresh(avatar)
            return avatar

    # ------------------------------------------------------------------
    def get_mood(self, avatar_id: int) -> Optional[int]:
        avatar = self.get_avatar(avatar_id)
        return avatar.mood if avatar else None
