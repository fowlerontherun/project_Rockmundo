
class Album:
    def __init__(self, id, title, album_type, genre_id, band_id, release_date=None,
                 song_ids=None, distribution_channels=None, cover_art=None):
        self.id = id
        self.title = title
        self.album_type = album_type
        self.genre_id = genre_id
        self.band_id = band_id
        self.release_date = release_date
        self.song_ids = song_ids or []
        self.distribution_channels = distribution_channels or ['digital']
        self.cover_art = cover_art

    def to_dict(self):
        return self.__dict__
