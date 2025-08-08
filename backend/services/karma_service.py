
from models.karma_event import KarmaEvent
from datetime import datetime

class KarmaService:
    def __init__(self, db):
        self.db = db

    def adjust_karma(self, user_id, amount, reason, source):
        event = KarmaEvent(
            id=None,
            user_id=user_id,
            amount=amount,
            reason=reason,
            source=source,
            timestamp=datetime.utcnow().isoformat()
        )
        self.db.insert_karma_event(event)
        self.db.update_user_karma(user_id, amount)

    def get_karma_history(self, user_id):
        return self.db.get_karma_events(user_id)

    def get_user_karma(self, user_id):
        return self.db.get_user_karma_total(user_id)
