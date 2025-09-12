
from datetime import datetime

class FanInteraction:
    def __init__(self, id, band_id, fan_id, interaction_type, content, created_at=None):
        self.id = id
        self.band_id = band_id
        self.fan_id = fan_id
        self.interaction_type = interaction_type  # e.g., 'petition', 'vote', 'feedback'
        self.content = content
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
