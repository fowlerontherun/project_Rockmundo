
from datetime import datetime

class AdminAction:
    def __init__(self, id, admin_id, action_type, payload, timestamp=None):
        self.id = id
        self.admin_id = admin_id
        self.action_type = action_type
        self.payload = payload
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
