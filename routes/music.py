from fastapi import APIRouter, Depends, HTTPException
from fastapi import Depends
from backend.auth.dependencies import get_current_user_id, require_permission
from sqlalchemy.orm import Session

from models.music import Song, Album, album_song_link
from schemas.music import (
    SongCreate, SongResponse,
    AlbumCreate, AlbumResponse
)
from database import get_db
from utils.i18n import _

router = APIRouter(prefix="/music", tags=["Music"])

@router.post("/songs", response_model=SongResponse, dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))])
def create_song(song: SongCreate, db: Session = Depends(get_db, user_id: int = Depends(get_current_user_id))):
    if not (song.band_id or song.collaboration_id):
        raise HTTPException(status_code=400, detail=_("Must provide band_id or collaboration_id"))
    new_song = Song(**song.dict())
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return new_song

@router.get("/songs/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db, user_id: int = Depends(get_current_user_id))):
    song = db.query(Song).get(song_id)
    if not song:
        raise HTTPException(status_code=404, detail=_("Song not found"))
    return song

@router.post("/albums", response_model=AlbumResponse)
def create_album(album: AlbumCreate, db: Session = Depends(get_db, user_id: int = Depends(get_current_user_id))):
    if not (album.band_id or album.collaboration_id):
        raise HTTPException(status_code=400, detail=_("Must provide band_id or collaboration_id"))
    
    if album.type == "ep" and len(album.song_ids) > 4:
        raise HTTPException(status_code=400, detail=_("EPs can have a maximum of 4 songs"))

    new_album = Album(
        title=album.title,
        type=album.type,
        band_id=album.band_id,
        collaboration_id=album.collaboration_id
    )
    db.add(new_album)
    db.commit()
    db.refresh(new_album)

    # Link songs
    for song_id in album.song_ids:
        song = db.query(Song).get(song_id)
        if song:
            db.execute(album_song_link.insert().values(album_id=new_album.id, song_id=song_id))
    db.commit()

    return AlbumResponse(
        id=new_album.id,
        title=new_album.title,
        type=new_album.type,
        release_date=new_album.release_date,
        song_ids=album.song_ids
    )