
from datetime import datetime

class CommunityKarma:
    def __init__(self, id, user_id, karma_score=0, last_updated=None):
        self.id = id
        self.user_id = user_id
        self.karma_score = karma_score
        self.last_updated = last_updated or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
