
from datetime import datetime

class KarmaEvent:
    def __init__(self, id, user_id, amount, reason, source, timestamp=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount  # + or -
        self.reason = reason
        self.source = source  # e.g., 'report', 'event', 'system'
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
