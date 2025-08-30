
from datetime import datetime

from models.karma_event import KarmaEvent
from services.xp_reward_service import xp_reward_service


class KarmaService:
    def __init__(self, db):
        self.db = db

    def adjust_karma(self, user_id, amount, reason, source, grant_xp: bool = False):
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
        if grant_xp and amount > 0:
            xp_reward_service.grant_hidden_xp(user_id, reason="karma", amount=int(amount))

    def get_karma_history(self, user_id):
        return self.db.get_karma_events(user_id)

    def get_user_karma(self, user_id):
        return self.db.get_user_karma_total(user_id)
