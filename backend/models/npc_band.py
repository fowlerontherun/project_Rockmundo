
from datetime import datetime

class NPCBand:
    def __init__(self, id, name, genre, activity_level, fame, last_active=None):
        self.id = id
        self.name = name
        self.genre = genre
        self.activity_level = activity_level  # 1-10, determines loop frequency
        self.fame = fame
        self.last_active = last_active or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
