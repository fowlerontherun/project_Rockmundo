
from datetime import datetime


class LivePerformance:
    def __init__(
        self,
        id,
        band_id,
        city,
        venue,
        date,
        setlist,
        crowd_size,
        fame_earned,
        revenue_earned,
        skill_gain,
        merch_sold,
        performance_score: float | None = None,
    ):
        self.id = id
        self.band_id = band_id
        self.city = city
        self.venue = venue
        self.date = date or datetime.utcnow().isoformat()
        self.setlist = setlist
        self.crowd_size = crowd_size
        self.fame_earned = fame_earned
        self.revenue_earned = revenue_earned
        self.skill_gain = skill_gain
        self.merch_sold = merch_sold
        # Optional quality metric for comparing performances
        self.performance_score = performance_score

    def to_dict(self):
        return self.__dict__
