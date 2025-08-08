
from models.album import Album

class AlbumService:
    def __init__(self, db):
        self.db = db

    def create_album(self, data):
        song_ids = data.get('song_ids', [])
        if data['album_type'] == 'EP' and len(song_ids) > 4:
            raise ValueError("EPs cannot have more than 4 songs")
        album = Album(**data)
        self.db.insert_album(album)
        return album.to_dict()

    def list_albums_by_band(self, band_id):
        return self.db.get_albums_by_band(band_id)

    def update_album(self, album_id, updates):
        self.db.update_album(album_id, updates)

    def publish_album(self, album_id):
        self.db.mark_album_released(album_id)
