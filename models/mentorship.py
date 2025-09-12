
from datetime import datetime

class Mentorship:
    def __init__(self, id, mentor_id, mentee_id, start_date=None, active=True):
        self.id = id
        self.mentor_id = mentor_id
        self.mentee_id = mentee_id
        self.start_date = start_date or datetime.utcnow().isoformat()
        self.active = active

    def to_dict(self):
        return self.__dict__
