
from datetime import datetime

class BandRelationship:
    def __init__(self, id, band_a_id, band_b_id, type, since=None, active=True):
        self.id = id
        self.band_a_id = band_a_id
        self.band_b_id = band_b_id
        self.type = type  # 'alliance' or 'rivalry'
        self.since = since or datetime.utcnow().isoformat()
        self.active = active

    def to_dict(self):
        return self.__dict__
