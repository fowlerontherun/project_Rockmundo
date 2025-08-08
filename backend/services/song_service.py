
from models.song import Song

class SongService:
    def __init__(self, db):
        self.db = db

    def create_song(self, data):
        if sum(data.get('royalties_split', {}).values()) != 100:
            raise ValueError("Royalties must sum to 100%")
        song = Song(**data)
        self.db.insert_song(song)
        return song.to_dict()

    def list_songs_by_band(self, band_id):
        return self.db.get_songs_by_band(band_id)

    def update_song(self, song_id, updates):
        self.db.update_song(song_id, updates)

    def delete_song(self, song_id):
        self.db.delete_song(song_id)
