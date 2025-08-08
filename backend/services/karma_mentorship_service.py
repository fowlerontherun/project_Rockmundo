
from models.community_karma import CommunityKarma
from models.mentorship import Mentorship
from datetime import datetime

class KarmaMentorshipService:
    def __init__(self, db):
        self.db = db

    def adjust_karma(self, user_id, delta):
        karma = self.db.get_karma_by_user(user_id)
        if not karma:
            karma = CommunityKarma(id=None, user_id=user_id, karma_score=delta)
            self.db.insert_karma(karma)
        else:
            new_score = karma["karma_score"] + delta
            self.db.update_karma_score(user_id, new_score)
        return self.db.get_karma_by_user(user_id)

    def start_mentorship(self, mentor_id, mentee_id):
        mentorship = Mentorship(id=None, mentor_id=mentor_id, mentee_id=mentee_id)
        self.db.insert_mentorship(mentorship)
        self.adjust_karma(mentor_id, +5)
        return mentorship.to_dict()

    def end_mentorship(self, mentor_id, mentee_id):
        self.db.deactivate_mentorship(mentor_id, mentee_id)
        self.adjust_karma(mentor_id, +2)
        self.adjust_karma(mentee_id, +2)
        return {"status": "mentorship completed"}
