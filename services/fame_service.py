
from models.fame import FameEvent
from datetime import datetime

class FameService:
    def __init__(self, db):
        self.db = db

    def award_fame(self, band_id, source, amount, reason):
        event = FameEvent(
            id=None,
            band_id=band_id,
            source=source,
            amount=amount,
            reason=reason,
            timestamp=datetime.utcnow().isoformat()
        )
        self.db.insert_fame_event(event)
        self.db.increment_band_fame(band_id, amount)

    def get_fame_history(self, band_id):
        return self.db.get_fame_events(band_id)

    def get_total_fame(self, band_id):
        return self.db.get_band_fame_total(band_id)
