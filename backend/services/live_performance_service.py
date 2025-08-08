
from models.live_performance import LivePerformance
from datetime import datetime
import random

class LivePerformanceService:
    def __init__(self, db):
        self.db = db

    def simulate_gig(self, band_id, city, venue, setlist):
        crowd_size = random.randint(50, 1000)
        fame_earned = crowd_size // 10
        revenue_earned = crowd_size * 5
        skill_gain = len(setlist) * 0.5
        merch_sold = int(crowd_size * 0.2)

        performance = LivePerformance(
            id=None,
            band_id=band_id,
            city=city,
            venue=venue,
            date=datetime.utcnow().isoformat(),
            setlist=setlist,
            crowd_size=crowd_size,
            fame_earned=fame_earned,
            revenue_earned=revenue_earned,
            skill_gain=skill_gain,
            merch_sold=merch_sold
        )

        self.db.insert_live_performance(performance)
        self.db.increment_band_fame(band_id, fame_earned)
        self.db.add_band_revenue(band_id, revenue_earned)
        self.db.increment_band_skill(band_id, skill_gain)
        self.db.increment_merch_sales(band_id, merch_sold)

        return performance.to_dict()

    def get_band_performances(self, band_id):
        return self.db.get_live_performances_by_band(band_id)
