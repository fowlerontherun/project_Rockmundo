from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.character import Base as CharacterBase
from models.avatar import Base as AvatarBase

DATABASE_URL = "sqlite:///./rockmundo.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
CharacterBase.metadata.create_all(bind=engine)
AvatarBase.metadata.create_all(bind=engine)
