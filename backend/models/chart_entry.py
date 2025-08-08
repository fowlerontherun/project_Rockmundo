
from datetime import datetime

class ChartEntry:
    def __init__(self, id, song_id, band_id, chart_type, position, week_start):
        self.id = id
        self.song_id = song_id
        self.band_id = band_id
        self.chart_type = chart_type  # e.g., Global Top 100, Digital Sales, Vinyl, Streaming
        self.position = position
        self.week_start = week_start or datetime.utcnow().date().isoformat()

    def to_dict(self):
        return self.__dict__
