
from datetime import datetime

class WorldPulse:
    def __init__(self, id, trending_genres, karma_level, active_events, top_players, updated_at=None):
        self.id = id
        self.trending_genres = trending_genres  # list of genre strings
        self.karma_level = karma_level  # e.g., 'Peaceful', 'Chaotic'
        self.active_events = active_events  # list of event titles
        self.top_players = top_players  # list of usernames or ids
        self.updated_at = updated_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
