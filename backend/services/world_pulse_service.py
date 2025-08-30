
from models.world_pulse import WorldPulse
from datetime import datetime

class WorldPulseService:
    def __init__(self, db):
        self.db = db

    def generate_world_pulse(self):
        genres = self.db.get_trending_genres_by_id()
        karma = self.db.get_average_karma()
        events = self.db.get_current_events()
        top_players = self.db.get_top_players()

        pulse = WorldPulse(
            id=None,
            trending_genres=genres,
            karma_level=self._calculate_karma_level(karma),
            active_events=[e["title"] for e in events],
            top_players=top_players
        )

        self.db.insert_world_pulse(pulse)
        return pulse.to_dict()

    def _calculate_karma_level(self, avg_karma):
        if avg_karma >= 80:
            return "Peaceful"
        elif avg_karma >= 50:
            return "Active"
        else:
            return "Chaotic"
