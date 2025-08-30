import random

from seeds.skill_seed import SKILL_NAME_TO_ID

from backend.models.random_event import RandomEvent
from backend.models.skill import Skill
from backend.services.notifications_service import NotificationsService
from backend.services.skill_service import skill_service


class RandomEventService:
    """Service to generate and apply random events."""

    def __init__(self, db, notifier: NotificationsService | None = None):
        self.db = db
        self.notifier = notifier or NotificationsService()

    # ------------------------------------------------------------------
    # Trigger helpers
    # ------------------------------------------------------------------
    def trigger_event_for_band(self, band_id: int, user_id: int | None = None):
        options = [
            (
                "delay",
                "Vehicle breakdown caused a delay.",
                {"skill": ("stamina", -5)},
            ),
            (
                "press",
                "Local press covered the band’s arrival.",
                {"fame": 10},
            ),
            (
                "fan_interaction",
                "Fans welcomed the band at the venue.",
                {"funds": 50},
            ),
        ]
        return self._trigger(band_id=band_id, avatar_id=None, user_id=user_id, options=options)

    def trigger_event_for_avatar(self, avatar_id: int, user_id: int | None = None):
        options = [
            (
                "street_performance",
                "You impressed passersby with a street solo.",
                {"fame": 5, "funds": 20},
            ),
            (
                "practice",
                "Extra practice boosted your skills.",
                {"skill": ("guitar", 2)},
            ),
        ]
        return self._trigger(band_id=None, avatar_id=avatar_id, user_id=user_id, options=options)

    def _trigger(self, band_id, avatar_id, user_id, options):
        selected = random.choice(options)
        impact = selected[2]
        skill_name, skill_delta = impact.get("skill", (None, 0))
        event = RandomEvent(
            id=None,
            band_id=band_id,
            avatar_id=avatar_id,
            type=selected[0],
            description=selected[1],
            fame=impact.get("fame", 0),
            funds=impact.get("funds", 0),
            skill=skill_name,
            skill_delta=skill_delta,
        )
        if self.db:
            self.db.insert_random_event(event)
        self._apply_impact(event)
        if user_id is not None:
            title = f"{event.type.replace('_', ' ').title()}"
            self.notifier.create(user_id, title, event.description)
        return event.to_dict()

    # ------------------------------------------------------------------
    # Impact application
    # ------------------------------------------------------------------
    def _apply_impact(self, event: RandomEvent):
        if self.db is None:
            return
        if event.band_id:
            if event.fame:
                self.db.increase_band_fame(event.band_id, event.fame)
            if event.funds:
                self.db.increase_band_funds(event.band_id, event.funds)
        if event.avatar_id:
            if event.fame:
                getattr(self.db, "increase_avatar_fame", lambda *_: None)(event.avatar_id, event.fame)
            if event.funds:
                getattr(self.db, "increase_avatar_funds", lambda *_: None)(event.avatar_id, event.funds)

        if event.skill and event.skill_delta:
            skill_id = SKILL_NAME_TO_ID.get(event.skill)
            if skill_id is None:
                return
            if event.skill_delta >= 0:
                skill_service.train(
                    event.band_id or event.avatar_id,
                    Skill(id=skill_id, name=event.skill, category="event"),
                    event.skill_delta,
                )
            else:
                skill_service.apply_decay(
                    event.band_id or event.avatar_id, skill_id, -event.skill_delta
                )

    # ------------------------------------------------------------------
    # Scheduler hook
    # ------------------------------------------------------------------
    def run_scheduled_events(self) -> int:
        """Trigger events across all bands/avatars with a probability."""
        if self.db is None:
            return 0
        triggered = 0
        for band_id in getattr(self.db, "list_band_ids", lambda: [])():
            if random.random() < 0.1:
                self.trigger_event_for_band(band_id)
                triggered += 1
        for avatar_id in getattr(self.db, "list_avatar_ids", lambda: [])():
            if random.random() < 0.05:
                self.trigger_event_for_avatar(avatar_id)
                triggered += 1
        return triggered


# Singleton instance used by background jobs
random_event_service = RandomEventService(db=None)
