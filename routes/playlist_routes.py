from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.playlist import Playlist

router = APIRouter()

# In-memory storage for playlists
playlists: Dict[int, Playlist] = {}
_next_id = 1


class PlaylistCreate(BaseModel):
    name: str
    is_public: bool = False


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    is_public: Optional[bool] = None


class PlaylistOut(BaseModel):
    id: int
    name: str
    song_ids: List[int]
    is_public: bool = False


class SongIn(BaseModel):
    song_id: int


@router.post("/playlists", response_model=PlaylistOut)
def create_playlist(payload: PlaylistCreate) -> PlaylistOut:
    global _next_id
    pl = Playlist(id=_next_id, name=payload.name, is_public=payload.is_public)
    playlists[_next_id] = pl
    _next_id += 1
    return PlaylistOut(**pl.to_dict())


@router.get("/playlists", response_model=List[PlaylistOut])
def list_playlists() -> List[PlaylistOut]:
    return [PlaylistOut(**p.to_dict()) for p in playlists.values()]


@router.get("/playlists/{playlist_id}", response_model=PlaylistOut)
def get_playlist(playlist_id: int) -> PlaylistOut:
    pl = playlists.get(playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return PlaylistOut(**pl.to_dict())


@router.put("/playlists/{playlist_id}", status_code=204)
def update_playlist(playlist_id: int, payload: PlaylistUpdate) -> None:
    pl = playlists.get(playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if payload.name is not None:
        pl.name = payload.name
    if payload.is_public is not None:
        pl.is_public = payload.is_public


@router.delete("/playlists/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: int) -> None:
    if playlist_id not in playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    del playlists[playlist_id]


@router.post("/playlists/{playlist_id}/songs", status_code=204)
def add_song_to_playlist(playlist_id: int, song: SongIn) -> None:
    pl = playlists.get(playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Playlist not found")
    pl.add_song(song.song_id)


@router.delete("/playlists/{playlist_id}/songs/{song_id}", status_code=204)
def remove_song_from_playlist(playlist_id: int, song_id: int) -> None:
    pl = playlists.get(playlist_id)
    if not pl:
        raise HTTPException(status_code=404, detail="Playlist not found")
    pl.remove_song(song_id)


@router.get("/playlists/public", response_model=List[PlaylistOut])
def list_public_playlists() -> List[PlaylistOut]:
    return [PlaylistOut(**p.to_dict()) for p in playlists.values() if p.is_public]


@router.get("/playlists/public/{playlist_id}", response_model=PlaylistOut)
def get_public_playlist(playlist_id: int) -> PlaylistOut:
    pl = playlists.get(playlist_id)
    if not pl or not pl.is_public:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return PlaylistOut(**pl.to_dict())


# Fan-facing endpoints exposing public playlists
@router.get("/playlists/fans", response_model=List[PlaylistOut])
def list_fan_playlists() -> List[PlaylistOut]:
    """List all playlists created by fans that are marked public."""
    return list_public_playlists()


@router.get("/playlists/fans/{playlist_id}", response_model=PlaylistOut)
def get_fan_playlist(playlist_id: int) -> PlaylistOut:
    """Retrieve a specific fan-created public playlist."""
    return get_public_playlist(playlist_id)
