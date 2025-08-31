
from datetime import datetime
from typing import List, Optional

from backend.models.arrangement import ArrangementTrack


class Song:
    def __init__(
        self,
        id: int,
        title: str,
        duration_sec: int,
        genre_id: Optional[int],
        lyrics: str,
        owner_band_id: int,
        themes: Optional[List[str]] = None,
        chord_progression: str = "",
        album_art_url: Optional[str] = None,
        release_date: Optional[str] = None,
        format: str = "digital",
        royalties_split: Optional[dict] = None,
        plagiarism_warning: Optional[str] = None,
        arrangement: Optional[List[ArrangementTrack]] = None,
    ) -> None:
        self.id = id
        self.title = title
        self.duration_sec = duration_sec
        self.genre_id = genre_id
        self.lyrics = lyrics
        self.themes = themes or []
        self.chord_progression = chord_progression
        self.album_art_url = album_art_url
        self.owner_band_id = owner_band_id
        self.release_date = release_date or datetime.utcnow().isoformat()
        self.format = format
        self.royalties_split = royalties_split or {owner_band_id: 100}
        self.plagiarism_warning = plagiarism_warning
        self.arrangement = arrangement or []

    def to_dict(self):
        data = self.__dict__.copy()
        if self.arrangement:
            data["arrangement"] = [a.__dict__ for a in self.arrangement]
        return data
