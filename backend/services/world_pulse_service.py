
from models.world_pulse import WorldPulse
from datetime import datetime

try:  # pragma: no cover - import shim for tests vs runtime
    from services.jobs_world_pulse import WorldPulseService as GenrePulseService
except Exception:  # pragma: no cover
    from backend.services.jobs_world_pulse import WorldPulseService as GenrePulseService


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

    def store_top_10_snapshot(self, date: str | None = None) -> list[dict]:
        """Generate and persist a daily World Pulse snapshot.

        This helper is designed for scheduled jobs or an admin endpoint.  It
        delegates the heavy lifting to :mod:`jobs_world_pulse` which writes
        genre rankings to the ``genre_pulse_snapshots`` table.  The top ten
        results are returned for convenience.

        Parameters
        ----------
        date:
            Optional ``YYYY-MM-DD`` string.  Defaults to ``datetime.utcnow()``.

        Returns
        -------
        list[dict]
            Top ten ranked rows as returned by ``ui_ranked_list``.
        """

        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        job = GenrePulseService()
        job.run_daily(date)
        return job.ui_ranked_list(date=date, limit=10)

    def _calculate_karma_level(self, avg_karma):
        if avg_karma >= 80:
            return "Peaceful"
        elif avg_karma >= 50:
            return "Active"
        else:
            return "Chaotic"
