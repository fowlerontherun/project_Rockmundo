from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SongCreate(BaseModel):
    title: str
    genre: str
    duration: int
    difficulty: int
    lyrics: str
    band_id: Optional[int] = None
    collaboration_id: Optional[int] = None

class SongResponse(SongCreate):
    id: int
    release_date: datetime

    class Config:
        orm_mode = True

class AlbumCreate(BaseModel):
    title: str
    type: str  # "album" or "ep"
    band_id: Optional[int] = None
    collaboration_id: Optional[int] = None
    song_ids: List[int]  # list of song IDs

class AlbumResponse(BaseModel):
    id: int
    title: str
    type: str
    release_date: datetime
    song_ids: List[int]

    class Config:
        orm_mode = True
