
from models.stream import Stream

PLATFORM_PAYOUTS = {
    "Spotify": 0.003,
    "YouTube": 0.002,
    "AppleMusic": 0.005,
    "Bandcamp": 0.01
}

class StreamService:
    def __init__(self, db):
        self.db = db

    def record_stream(self, data):
        stream = Stream(**data)
        self.db.insert_stream(stream)
        self._apply_revenue(stream)
        return stream.to_dict()

    def _apply_revenue(self, stream):
        payout = PLATFORM_PAYOUTS.get(stream.platform, 0.003)
        song = self.db.get_song_by_id(stream.song_id)
        total_amount = payout
        for band_id, percent in song['royalties_split'].items():
            revenue = total_amount * (percent / 100)
            self.db.add_revenue_entry(band_id, stream.song_id, revenue, stream.timestamp)

    def get_band_revenue(self, band_id):
        return self.db.get_revenue_by_band(band_id)

    def get_song_streams(self, song_id):
        return self.db.get_streams_by_song(song_id)
