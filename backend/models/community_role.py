
from datetime import datetime

class CommunityRole:
    def __init__(self, id, role_name, holder_id, type, assigned_at=None):
        self.id = id
        self.role_name = role_name
        self.holder_id = holder_id  # NPC or player ID
        self.type = type  # 'npc' or 'player'
        self.assigned_at = assigned_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
