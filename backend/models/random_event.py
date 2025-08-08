
from datetime import datetime

class RandomEvent:
    def __init__(self, id, band_id, type, description, impact, triggered_at=None):
        self.id = id
        self.band_id = band_id
        self.type = type  # e.g., 'delay', 'press', 'fan_interaction'
        self.description = description
        self.impact = impact  # text describing impact on fame, funds, or fatigue
        self.triggered_at = triggered_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
