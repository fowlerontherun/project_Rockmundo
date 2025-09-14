"""Album service using SQLAlchemy sessions.

This module replaces the previous ``sqlite3`` implementation with a session
based approach similar to :mod:`services.band_service`.  The service exposes
helpers to create, list, update and publish music releases.  Earnings are
delegated to :class:`services.band_service.BandService` so tests may share the
same in-memory database by providing a custom ``session_factory``.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from models.music import Base as MusicBase  # noqa: F401
from models.music import Release, Track
from services.band_service import (  # noqa: F401
    BandCollaboration,
    BandService,
)
from sqlalchemy import create_engine, or_, func
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "rockmundo.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Tables are created by the application or tests.  Creating them here would
# require resolving cross-metadata foreign keys (``Release`` references tables
# from ``BandBase``), so we leave schema creation to the caller.


# ---------------------------------------------------------------------------
# Service implementation
# ---------------------------------------------------------------------------


class AlbumService:
    """Encapsulates release CRUD operations and publishing logic."""

    def __init__(
        self,
        session_factory: Callable[[], Session] | sessionmaker = SessionLocal,
        band_service: BandService | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.band_service = band_service or BandService(session_factory)

    # ------------------------------------------------------------------
    def create_release(self, data: dict) -> dict:
        """Create a new music release along with its tracks."""

        release_format = data.get("format")
        album_type = data.get("album_type", "studio")
        tracks: Iterable[dict] = data.get("tracks", [])

        # ``tracks`` may be provided as an iterator; materialize it once so we
        # can validate length and reuse the data.
        tracks = list(tracks)
        if release_format == "ep" and len(tracks) > 4:
            raise ValueError("EPs cannot contain more than 4 tracks")
        if album_type == "live" and release_format in {"single", "ep"}:
            raise ValueError("Live recordings can only be released as full albums")

        total_runtime = sum(t.get("duration", 0) for t in tracks)
        distribution_channels = ",".join(data.get("distribution_channels", []))

        with self.session_factory() as session:
            with session.begin():
                if album_type == "live":
                    existing_live = (
                        session.query(Release)
                        .filter(
                            Release.band_id == data.get("band_id"),
                            Release.album_type == "live",
                            Release.release_date.isnot(None),
                            func.strftime("%Y", Release.release_date)
                            == str(datetime.utcnow().year),
                        )
                        .first()
                    )
                    if existing_live:
                        raise ValueError(
                            "Band already released a live album this year"
                        )

                release = Release(
                    band_id=data.get("band_id"),
                    collaboration_id=data.get("collaboration_id"),
                    title=data.get("title"),
                    format=release_format,
                    album_type=album_type,
                    total_runtime=total_runtime,
                    distribution_channels=distribution_channels,
                )
                session.add(release)
                session.flush()  # populate ``release.id``

                for i, track in enumerate(tracks, start=1):
                    session.add(
                        Track(
                            release_id=release.id,
                            title=track["title"],
                            duration=track.get("duration", 0),
                            track_number=i,
                        )
                    )

            session.refresh(release)
            return {"status": "ok", "release_id": release.id}

    # ------------------------------------------------------------------
    def list_releases_by_band(
        self,
        band_id: int,
        search: str | None = None,
        sort: str | None = None,
    ) -> list[dict]:
        """List releases belonging to the band or its collaborations."""

        with self.session_factory() as session:
            query = (
                session.query(Release)
                .outerjoin(
                    BandCollaboration,
                    Release.collaboration_id == BandCollaboration.id,
                )
                .filter(
                    or_(
                        Release.band_id == band_id,
                        BandCollaboration.band_1_id == band_id,
                        BandCollaboration.band_2_id == band_id,
                    )
                )
            )
            if search:
                query = query.filter(Release.title.ilike(f"%{search}%"))
            if sort == "title":
                query = query.order_by(Release.title)
            else:
                query = query.order_by(Release.release_date.desc())
            releases = query.all()

            result: list[dict] = []
            for r in releases:
                result.append(
                    {
                        "release_id": r.id,
                        "title": r.title,
                        "format": r.format,
                        "album_type": r.album_type,
                        "release_date": r.release_date.isoformat()
                        if r.release_date
                        else None,
                        "total_runtime": r.total_runtime,
                        "distribution_channels": r.distribution_channels,
                    }
                )
            return result

    def search_releases(self, query: str, page: int = 1, limit: int = 10) -> list[dict]:
        """Search albums by title with basic fuzzy matching and pagination."""
        with self.session_factory() as session:
            q = (
                session.query(Release)
                .filter(Release.title.ilike(f"%{query}%"))
                .order_by(Release.title.asc())
            )
            releases = q.offset((page - 1) * limit).limit(limit).all()
            return [
                {
                    "release_id": r.id,
                    "title": r.title,
                }
                for r in releases
            ]

    # ------------------------------------------------------------------
    def update_release(self, release_id: int, updates: dict) -> dict:
        """Update fields on a release."""

        with self.session_factory() as session:
            with session.begin():
                release = session.get(Release, release_id)
                if not release:
                    return {"error": "Release not found"}
                for field, value in updates.items():
                    setattr(release, field, value)
            return {"status": "ok", "message": "Release updated"}

    # ------------------------------------------------------------------
    def publish_release(self, release_id: int) -> dict:
        """Mark a release as published and compute earnings."""

        with self.session_factory() as session:
            with session.begin():
                release = session.get(Release, release_id)
                if not release:
                    return {"error": "Release not found"}
                if release.album_type == "live" and release.format in {"single", "ep"}:
                    return {
                        "error": "Live recordings can only be released as full albums"
                    }

                release_date = datetime.utcnow()
                release.release_date = release_date

                band_id = release.band_id
                collab_band_id = None
                if release.collaboration_id:
                    collab = session.get(
                        BandCollaboration, release.collaboration_id
                    )
                    if collab:
                        # Determine the partner band for revenue splitting
                        if band_id == collab.band_1_id or band_id is None:
                            band_id = collab.band_1_id
                            collab_band_id = collab.band_2_id
                        else:
                            collab_band_id = collab.band_1_id

        fame_gain = 50
        revenue = 1000
        earnings = self.band_service.split_earnings(
            band_id, revenue, collab_band_id
        )

        return {
            "status": "ok",
            "release_date": release_date.isoformat(),
            "fame_gain": fame_gain,
            "revenue": revenue,
            "earnings": earnings,
        }


__all__ = ["AlbumService"]

