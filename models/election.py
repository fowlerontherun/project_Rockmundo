
from datetime import datetime

class Election:
    def __init__(self, id, role_name, candidates, votes, status, ends_at):
        self.id = id
        self.role_name = role_name
        self.candidates = candidates  # list of user IDs or NPC IDs
        self.votes = votes  # dict of candidate_id -> vote count
        self.status = status  # 'open', 'closed'
        self.ends_at = ends_at

    def to_dict(self):
        return self.__dict__
