
class Album:
    def __init__(
        self,
        id,
        title,
        album_type,
        genre_id,
        band_id,
        release_date=None,
        songs=None,
        distribution_channels=None,
        cover_art=None,
    ):
        self.id = id
        self.title = title
        self.album_type = album_type
        self.genre_id = genre_id
        self.band_id = band_id
        self.release_date = release_date
        # ``songs`` is a list of dicts: {"song_id", "show_id", "performance_score"}
        self.songs = songs or []
        self.distribution_channels = distribution_channels or ["digital"]
        self.cover_art = cover_art

    def to_dict(self):
        return self.__dict__
