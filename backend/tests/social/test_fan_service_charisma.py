import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from backend.schemas.avatar import AvatarCreate
from services.avatar_service import AvatarService
from services import fan_service


def _setup_avatar(charisma: int) -> AvatarService:
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
            top_clothing="t",
            bottom_clothing="j",
            shoes="b",
            charisma=charisma,
        )
    )
    return svc


def test_charisma_impacts_fan_loyalty(tmp_path, monkeypatch):
    db_file = tmp_path / "fans.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
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

    avatar_service = _setup_avatar(80)
    monkeypatch.setattr(fan_service, "DB_PATH", db_file)
    monkeypatch.setattr(fan_service, "avatar_service", avatar_service)

    fan_service.add_fan(user_id=42, band_id=1, location="web")
    fan_service.add_fan(user_id=42, band_id=1, location="web")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT loyalty FROM fans WHERE band_id = 1")
    loyalty = cur.fetchone()[0]
    conn.close()

    assert loyalty == 47
