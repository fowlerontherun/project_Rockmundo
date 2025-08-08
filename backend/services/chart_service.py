
from models.chart_entry import ChartEntry
from collections import defaultdict
from datetime import datetime, timedelta

class ChartService:
    def __init__(self, db):
        self.db = db

    def calculate_weekly_charts(self):
        songs = self.db.get_all_songs()
        stream_data = self.db.get_streams_in_date_range(
            (datetime.utcnow() - timedelta(days=7)).isoformat(),
            datetime.utcnow().isoformat()
        )
        revenue_data = self.db.get_revenue_in_date_range(
            (datetime.utcnow() - timedelta(days=7)).isoformat(),
            datetime.utcnow().isoformat()
        )

        song_scores = defaultdict(float)

        for stream in stream_data:
            song_scores[stream['song_id']] += 1  # basic stream weight

        for rev in revenue_data:
            song_scores[rev['song_id']] += rev['amount'] * 10  # weight revenue higher

        sorted_songs = sorted(song_scores.items(), key=lambda x: x[1], reverse=True)

        week_start = datetime.utcnow().date().isoformat()
        for i, (song_id, score) in enumerate(sorted_songs[:100], start=1):
            song = self.db.get_song_by_id(song_id)
            chart_entry = ChartEntry(
                id=None,
                song_id=song_id,
                band_id=song['owner_band_id'],
                chart_type="Global Top 100",
                position=i,
                week_start=week_start
            )
            self.db.insert_chart_entry(chart_entry)

    def get_chart(self, chart_type, week_start):
        return self.db.get_chart_entries(chart_type, week_start)
