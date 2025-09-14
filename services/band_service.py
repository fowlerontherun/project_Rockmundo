"""Band service using SQLAlchemy sessions.

This module replaces the previous raw ``sqlite3`` implementation with a
session based approach.  All public functions delegate to an internal
``BandService`` class which manages database interactions through SQLAlchemy
and ensures that operations that modify membership or compute revenue splits
are executed atomically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.services.chemistry_service import ChemistryService
from backend.services.band_relationship_service import BandRelationshipService
from backend.services.avatar_service import AvatarService
from backend.services.skill_service import SkillService
from models.skill import Skill

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "rockmundo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


class Band(Base):
    """Simple band model used by the service layer."""

    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    genre = Column(String)
    founder_id = Column(Integer, index=True)
    fame = Column(Integer, default=0)
    formed_at = Column(DateTime(timezone=True), server_default=func.now())


class BandMember(Base):
    __tablename__ = "band_members"

    id = Column(Integer, primary_key=True, index=True)
    band_id = Column(Integer, ForeignKey("bands.id"))
    user_id = Column(Integer, index=True)
    role = Column(String)


class BandCollaboration(Base):
    __tablename__ = "band_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    band_1_id = Column(Integer, index=True)
    band_2_id = Column(Integer, index=True)
    project_type = Column(String)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Create tables for the default engine.  Tests can create their own engine and
# call ``Base.metadata.create_all`` on it when using a custom session factory.
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Service implementation
# ---------------------------------------------------------------------------


class BandService:
    """Service layer providing band management helpers."""

    def __init__(
        self,
        session_factory: Callable[[], Session] | sessionmaker = SessionLocal,
        chemistry_service: ChemistryService | None = None,
        relationship_service: BandRelationshipService | None = None,
        avatar_service: AvatarService | None = None,
        skill_service: SkillService | None = None,
    ):
        self.session_factory = session_factory
        self.chemistry_service = chemistry_service or ChemistryService(session_factory)
        self.relationship_service = relationship_service or BandRelationshipService()
        self.avatar_service = avatar_service or AvatarService()
        self.skill_service = skill_service or SkillService(avatar_service=self.avatar_service)

    # ------------------------------------------------------------------
    def create_band(self, user_id: int, band_name: str, genre: str) -> Band:
        """Create a new band and add the founder as the first member."""

        with self.session_factory() as session:
            with session.begin():
                band = Band(name=band_name, genre=genre, founder_id=user_id, fame=0)
                session.add(band)
                session.flush()  # populate ``band.id``
                session.add(BandMember(band_id=band.id, user_id=user_id, role="founder"))
            session.refresh(band)
            return band

    # ------------------------------------------------------------------
    def add_member(self, band_id: int, user_id: int, role: str = "member") -> None:
        """Add a member to the band if not already present."""

        with self.session_factory() as session:
            with session.begin():
                exists = (
                    session.query(BandMember)
                    .filter_by(band_id=band_id, user_id=user_id)
                    .first()
                )
                if exists:
                    return
                existing_members = [
                    uid
                    for (uid,) in session.query(BandMember.user_id).filter_by(
                        band_id=band_id
                    )
                ]
                session.add(BandMember(band_id=band_id, user_id=user_id, role=role))

        for uid in existing_members:
            self.chemistry_service.initialize_pair(user_id, uid)

    # ------------------------------------------------------------------
    def remove_member(self, band_id: int, user_id: int) -> None:
        """Remove a member from the band."""

        with self.session_factory() as session:
            with session.begin():
                session.query(BandMember).filter_by(band_id=band_id, user_id=user_id).delete()

    # ------------------------------------------------------------------
    def get_band_info(self, band_id: int) -> Optional[dict]:
        """Retrieve band information and membership list."""

        with self.session_factory() as session:
            band = session.get(Band, band_id)
            if not band:
                return None

            members = (
                session.query(BandMember.user_id, BandMember.role)
                .filter_by(band_id=band_id)
                .all()
            )
            return {
                "id": band.id,
                "name": band.name,
                "genre": band.genre,
                "fame": band.fame,
                "founder_id": band.founder_id,
                "formed_at": band.formed_at,
                "members": [
                    {"user_id": uid, "role": role} for uid, role in members
                ],
            }

    # ------------------------------------------------------------------
    def _average_leadership(self, band_id: int) -> float:
        with self.session_factory() as session:
            members = [
                uid
                for (uid,) in session.query(BandMember.user_id).filter_by(
                    band_id=band_id
                )
            ]
        if not members:
            return 0.0
        total = 0
        for uid in members:
            avatar = self.avatar_service.get_avatar_by_character_id(uid)
            if avatar:
                total += avatar.leadership
        return total / len(members)

    # ------------------------------------------------------------------
    def decay_band_skills(self, band_id: int, amount: int) -> None:
        modifier = 1 - self._average_leadership(band_id) / 200
        with self.session_factory() as session:
            members = [
                uid
                for (uid,) in session.query(BandMember.user_id).filter_by(
                    band_id=band_id
                )
            ]
        for uid in members:
            self.skill_service.decay_skills(uid, int(amount * modifier))

    # ------------------------------------------------------------------
    def collective_training(self, band_id: int, skill: Skill, base_xp: int) -> None:
        modifier = 1 + self._average_leadership(band_id) / 200
        with self.session_factory() as session:
            members = [
                uid
                for (uid,) in session.query(BandMember.user_id).filter_by(
                    band_id=band_id
                )
            ]
        xp = int(base_xp * modifier)
        for uid in members:
            self.skill_service.train(uid, skill, xp)

    # ------------------------------------------------------------------
    def increment_fame(self, band_id: int, amount: int) -> None:
        """Increase a band's fame by ``amount``."""

        with self.session_factory() as session:
            with session.begin():
                band = session.get(Band, band_id)
                if band:
                    band.fame = (band.fame or 0) + amount

    # ------------------------------------------------------------------
    def split_earnings(
        self, band_id: int, amount: int, collaboration_band_id: int | None = None
    ) -> dict:
        """Compute revenue splits.

        If ``collaboration_band_id`` is provided, the amount is split 50/50
        between the two bands.  Otherwise the earnings are divided equally among
        current members of the band.  Reads are wrapped in a transaction to
        provide a consistent snapshot.
        """

        if collaboration_band_id:
            modifier = 1.0
            if self.relationship_service:
                modifier = self.relationship_service.get_relationship_modifier(
                    band_id, collaboration_band_id
                )
            total = int(amount * modifier)
            return {
                "band_1_share": total // 2,
                "band_2_share": total - (total // 2),
                "modifier": modifier,
            }

        with self.session_factory() as session:
            with session.begin():
                members = [
                    uid
                    for (uid,) in session.query(BandMember.user_id).filter_by(band_id=band_id)
                ]

        num_members = len(members)
        share = amount // num_members if num_members else 0
        payouts = {uid: share for uid in members}
        return {"total": amount, "per_member": share, "payouts": payouts}

    # ------------------------------------------------------------------
    def share_band(self, user_a: int, user_b: int) -> bool:
        """Return True if two users are members of the same band."""

        with self.session_factory() as session:
            bands_a = (
                session.query(BandMember.band_id)
                .filter_by(user_id=user_a)
                .subquery()
            )
            return (
                session.query(BandMember)
                .filter(BandMember.user_id == user_b, BandMember.band_id.in_(bands_a))
                .first()
                is not None
            )

    # ------------------------------------------------------------------
    def create_collaboration(
        self, band_1_id: int, band_2_id: int, project_type: str, title: str
    ) -> BandCollaboration:
        """Record a collaboration between two bands."""

        with self.session_factory() as session:
            with session.begin():
                collab = BandCollaboration(
                    band_1_id=band_1_id,
                    band_2_id=band_2_id,
                    project_type=project_type,
                    title=title,
                )
                session.add(collab)
            session.refresh(collab)
            return collab

    # ------------------------------------------------------------------
    def list_collaborations(self, band_id: int) -> list[BandCollaboration]:
        with self.session_factory() as session:
            return (
                session.query(BandCollaboration)
                .filter(
                    (BandCollaboration.band_1_id == band_id)
                    | (BandCollaboration.band_2_id == band_id)
                )
                .all()
            )

    def search_bands(self, query: str, page: int = 1, limit: int = 10) -> list[dict]:
        """Search bands by name with basic fuzzy matching and pagination."""
        with self.session_factory() as session:
            q = (
                session.query(Band)
                .filter(Band.name.ilike(f"%{query}%"))
                .order_by(Band.name.asc())
            )
            bands = q.offset((page - 1) * limit).limit(limit).all()
            return [
                {
                    "id": b.id,
                    "name": b.name,
                    "founder_id": b.founder_id,
                    "genre": b.genre,
                    "formed_at": b.formed_at,
                }
                for b in bands
            ]

    # ------------------------------------------------------------------
    def get_band_collaborations(self, band_id: int) -> list[dict]:
        """Compatibility wrapper returning collaborations as dictionaries."""

        collabs = self.list_collaborations(band_id)
        return [
            {
                "album_id": c.id,
                "title": c.title,
                "release_date": c.created_at,
                "collab_band_id": c.band_2_id if c.band_1_id == band_id else c.band_1_id,
            }
            for c in collabs
        ]


# Default service instance -------------------------------------------------
_service = BandService()


# Module level functions kept for backwards compatibility ------------------


def create_band(user_id: int, band_name: str, genre: str) -> Band:
    return _service.create_band(user_id, band_name, genre)


def add_member(band_id: int, user_id: int, role: str = "member") -> dict:
    _service.add_member(band_id, user_id, role)
    return {"status": "ok", "message": "Member added"}


def remove_member(band_id: int, user_id: int) -> dict:
    _service.remove_member(band_id, user_id)
    return {"status": "ok", "message": "Member removed"}


def get_band_info(band_id: int) -> Optional[dict]:
    return _service.get_band_info(band_id)


def split_earnings(band_id: int, amount: int, collaboration_band_id: int | None = None) -> dict:
    return _service.split_earnings(band_id, amount, collaboration_band_id)


def decay_band_skills(band_id: int, amount: int) -> None:
    _service.decay_band_skills(band_id, amount)


def collective_training(band_id: int, skill: Skill, base_xp: int) -> None:
    _service.collective_training(band_id, skill, base_xp)


def get_band_collaborations(band_id: int) -> list[dict]:
    return _service.get_band_collaborations(band_id)


def share_band(user_a: int, user_b: int) -> bool:
    return _service.share_band(user_a, user_b)


def increment_fame(band_id: int, amount: int) -> None:
    _service.increment_fame(band_id, amount)


__all__ = [
    "BandService",
    "Band",
    "BandMember",
    "BandCollaboration",
    "create_band",
    "add_member",
    "remove_member",
    "get_band_info",
    "split_earnings",
    "decay_band_skills",
    "collective_training",
    "increment_fame",
    "get_band_collaborations",
    "share_band",
]

