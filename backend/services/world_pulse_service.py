
from models.world_pulse import WorldPulse
from datetime import datetime


def get_current_season(now: datetime | None = None) -> str:
    """Return the meteorological season for ``now``.

    The helper defaults to :func:`datetime.utcnow` when ``now`` is ``None`` and
    maps the month to one of ``Spring``, ``Summer``, ``Autumn`` or ``Winter``.
    This logic is shared by multiple services that need to reason about the
    current season.
    """

    now = now or datetime.utcnow()
    month = now.month
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"

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
            top_players=top_players,
            season=get_current_season(),
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
