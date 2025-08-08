
from datetime import datetime

class FameEvent:
    def __init__(self, id, band_id, source, amount, reason, timestamp=None):
        self.id = id
        self.band_id = band_id
        self.source = source  # e.g., 'stream', 'gig', 'press', 'karma'
        self.amount = amount
        self.reason = reason
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
