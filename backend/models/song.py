
from datetime import datetime

class Song:
    def __init__(self, id, title, duration_sec, genre_id, lyrics, owner_band_id,
                 release_date=None, format='digital', royalties_split=None):
        self.id = id
        self.title = title
        self.duration_sec = duration_sec
        self.genre_id = genre_id
        self.lyrics = lyrics
        self.owner_band_id = owner_band_id
        self.release_date = release_date or datetime.utcnow().isoformat()
        self.format = format
        self.royalties_split = royalties_split or {owner_band_id: 100}

    def to_dict(self):
        return self.__dict__
