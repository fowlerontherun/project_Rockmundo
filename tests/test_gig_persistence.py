import sqlite3
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoReferencedTableError

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))


def _setup_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE gigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue_size INTEGER,
            date TEXT,
            ticket_price INTEGER,
            status TEXT,
            attendance INTEGER,
            revenue INTEGER,
            fame_gain INTEGER
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE fans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            band_id INTEGER,
            location TEXT,
            loyalty INTEGER,
            source TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def test_gig_completion_persists_services(monkeypatch, tmp_path):
    from backend.services import gig_service as gs
    from backend.services import fan_service
    from backend.services.skill_service import SkillService
    from backend.services.band_service import BandService as BandSvc, Base as BandBase
    from backend.services.avatar_service import (
        AvatarService as AvatarSvc,
    )
    from backend.services.economy_service import EconomyService as EconSvc
    from backend.schemas.avatar import AvatarCreate
    from models.avatar import Base as AvatarBase
    from models import avatar_skin  # noqa: F401

    db = tmp_path / "gig.db"
    _setup_db(db)

    engine = create_engine(f"sqlite:///{db}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    BandBase.metadata.create_all(bind=engine)
    try:
        AvatarBase.metadata.create_all(bind=engine)
    except NoReferencedTableError:
        pass

    band_service = BandSvc(session_factory=SessionLocal)
    avatar_service = AvatarSvc(session_factory=SessionLocal)
    economy_service = EconSvc(db)
    economy_service.ensure_schema()

    monkeypatch.setattr(gs, "DB_PATH", db)
    monkeypatch.setattr(gs, "band_service", band_service)
    monkeypatch.setattr(gs, "avatar_service", avatar_service)
    monkeypatch.setattr(gs, "economy_service", economy_service)
    skill_service = SkillService(db_path=db, avatar_service=avatar_service)
    monkeypatch.setattr(gs, "skill_service", skill_service)

    monkeypatch.setattr(fan_service, "DB_PATH", db)
    monkeypatch.setattr(fan_service, "avatar_service", avatar_service)
    monkeypatch.setattr(gs.fan_service, "DB_PATH", db)
    monkeypatch.setattr(gs.fan_service, "avatar_service", avatar_service)

    avatar = avatar_service.create_avatar(
        AvatarCreate(
            character_id=1,
            nickname="Hero",
            body_type="avg",
            skin_tone="light",
            face_shape="oval",
            hair_style="short",
            hair_color="black",
            top_clothing="tee",
            bottom_clothing="jeans",
            shoes="sneakers",
        )
    )
    band = band_service.create_band(avatar.id, "The Heroes", "rock")

    for i in range(20):
        fan_service.add_fan(100 + i, band.id, "NY")

    monkeypatch.setattr(gs.random, "randint", lambda a, b: b)

    gs.create_gig(band.id, "NY", 100, "2024-01-01", 10)
    result = gs.simulate_gig_result(1)

    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT status, attendance, revenue, fame_gain FROM gigs WHERE id=1"
        ).fetchone()

    assert row == (
        "completed",
        result["attendance"],
        result["earnings"],
        result["fame_gain"],
    )

    band_info = band_service.get_band_info(band.id)
    assert band_info["fame"] == result["fame_gain"]

    balance = economy_service.get_balance(band.id)
    assert balance == result["earnings"]

    refreshed = avatar_service.get_avatar(avatar.id)
    assert refreshed.fatigue > 0

