from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Text, Table, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Link table between albums and songs
album_song_link = Table(
    "album_song_link",
    Base.metadata,
    Column("album_id", Integer, ForeignKey("albums.id")),
    Column("song_id", Integer, ForeignKey("songs.id"))
)

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    duration = Column(Integer)  # in seconds
    difficulty = Column(Integer)  # 1 to 10
    lyrics = Column(Text)

    band_id = Column(Integer, ForeignKey("bands.id"), nullable=True)
    collaboration_id = Column(Integer, ForeignKey("band_collaborations.id"), nullable=True)

    release_date = Column(DateTime(timezone=True), server_default=func.now())

class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String)  # "album" or "ep"
    release_date = Column(DateTime(timezone=True), server_default=func.now())

    band_id = Column(Integer, ForeignKey("bands.id"), nullable=True)
    collaboration_id = Column(Integer, ForeignKey("band_collaborations.id"), nullable=True)

    songs = relationship("Song", secondary=album_song_link)
