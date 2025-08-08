
from datetime import datetime

class AITourManager:
    def __init__(self, id, band_id, unlocked, optimization_level, active_since=None):
        self.id = id
        self.band_id = band_id
        self.unlocked = unlocked  # bool
        self.optimization_level = optimization_level  # 1 to 5
        self.active_since = active_since or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
