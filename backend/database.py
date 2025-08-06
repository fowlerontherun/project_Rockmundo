from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.character import Base as CharacterBase
from models.avatar import Base as AvatarBase
from models.skin import Base as SkinBase
from models.band import Base as BandBase
from models.music import Base as MusicBase
from models.distribution import Base as DistributionBase

DATABASE_URL = "sqlite:///./rockmundo.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
CharacterBase.metadata.create_all(bind=engine)
AvatarBase.metadata.create_all(bind=engine)
SkinBase.metadata.create_all(bind=engine)
BandBase.metadata.create_all(bind=engine)
MusicBase.metadata.create_all(bind=engine)
DistributionBase.metadata.create_all(bind=engine)
