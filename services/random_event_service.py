import random

from seeds.skill_seed import SKILL_NAME_TO_ID


from models.random_event import RandomEvent
from models.random_events import ADDICTION_EVENTS
from models.skill import Skill
from backend.services.addiction_service import addiction_service
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
    def trigger_event_for_band(
        self,
        band_id: int,
        user_id: int | None = None,
        *,
        location: str | None = None,
        mood: int | None = None,
        luck: int = 0,
    ):
        """Trigger a contextual event for a band."""

        options = [
            {
                "type": "delay",
                "description": "Vehicle breakdown caused a delay.",
                "impact": {"skill": ("stamina", -5)},
            },
            {
                "type": "traffic_jam",
                "description": "Heavy traffic slowed the band's travel.",
                "impact": {"skill": ("stamina", -2)},
            },
            {
                "type": "weather_delay",
                "description": "Severe weather forced a detour.",
                "impact": {"funds": -20},
            },
            {
                "type": "mechanical_issue",
                "description": "A mechanical issue required roadside repairs.",
                "impact": {"skill": ("stamina", -3)},
            },
            {
                "type": "press",
                "description": "Local press covered the band’s arrival.",
                "impact": {"fame": 10},
                "location": ["city", "venue"],
            },
            {
                "type": "fan_interaction",
                "description": "Fans welcomed the band at the venue.",
                "impact": {"funds": 50},
                "mood_range": (60, 100),
            },
            {
                "type": "local_cuisine",
                "description": "Sampled local cuisine, lifting spirits.",
                "impact": {"fame": 3},
                "location": ["city"],
                "mood_range": (0, 55),
            },
        ]
        return self._trigger(
            band_id=band_id,
            avatar_id=None,
            user_id=user_id,
            options=options,
            location=location,
            mood=mood,
            luck=luck,
        )

    def trigger_event_for_avatar(
        self,
        avatar_id: int,
        user_id: int | None = None,
        *,
        location: str | None = None,
        mood: int | None = None,
        luck: int = 0,
    ):
        options = [
            {
                "type": "street_performance",
                "description": "You impressed passersby with a street solo.",
                "impact": {"fame": 5, "funds": 20},
                "location": ["street"],
            },
            {
                "type": "practice",
                "description": "Extra practice boosted your skills.",
                "impact": {"skill": ("guitar", 2)},
                "mood_range": (50, 100),
            },
            {
                "type": "rainy_day_jam",
                "description": "A rainy day inspired a reflective jam session.",
                "impact": {"skill": ("songwriting", 1), "fame": 2},
                "location": ["indoors"],
                "mood_range": (20, 80),
            },
        ]
        return self._trigger(
            band_id=None,
            avatar_id=avatar_id,
            user_id=user_id,
            options=options,
            location=location,
            mood=mood,
            luck=luck,
        )

    def _trigger(
        self,
        band_id,
        avatar_id,
        user_id,
        options,
        *,
        location=None,
        mood=None,
        luck: int = 0,
    ):
        candidates = []
        weights = []
        for opt in options:
            locs = opt.get("location")
            mood_range = opt.get("mood_range")
            if locs and location not in locs:
                continue
            if mood_range and mood is not None:
                low, high = mood_range
                if not (low <= mood <= high):
                    continue
            candidates.append(opt)
            impact = opt.get("impact", {})
            positive = False
            for val in impact.values():
                if isinstance(val, (int, float)) and val > 0:
                    positive = True
                    break
            if not positive:
                skill = impact.get("skill")
                if isinstance(skill, (list, tuple)) and len(skill) > 1:
                    positive = skill[1] > 0
            weight = 1 + (luck / 100 if positive else 0)
            weights.append(weight)
        if not candidates:
            candidates = options
            weights = []
            for opt in candidates:
                impact = opt.get("impact", {})
                positive = any(
                    isinstance(v, (int, float)) and v > 0
                    for v in impact.values()
                )
                if not positive:
                    skill = impact.get("skill")
                    if isinstance(skill, (list, tuple)) and len(skill) > 1:
                        positive = skill[1] > 0
                weights.append(1 + (luck / 100 if positive else 0))
        selected = random.choices(candidates, weights=weights, k=1)[0]
        impact = selected.get("impact", {})
        skill_name, skill_delta = impact.get("skill", (None, 0))
        event = RandomEvent(
            id=None,
            band_id=band_id,
            avatar_id=avatar_id,
            type=selected["type"],
            description=selected["description"],
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
    # Addiction-related events
    # ------------------------------------------------------------------
    def trigger_addiction_event(
        self, user_id: int, *, level: int | None = None, date: str | None = None
    ):
        """Trigger negative events based on the user's addiction level.

        The caller may provide ``level`` to avoid an extra lookup.  The schedule
        is not modified here; callers decide how to handle any cancelled events.
        """

        level = level if level is not None else addiction_service.get_highest_level(user_id)
        if level < 50:
            return None
        if level >= 100:
            event_type = "overdose"
            description = "Severe overdose requires hospitalization."
        elif level >= 70:
            event_type = "police_intervention"
            description = "Police intervened due to erratic behavior."
        else:
            event_type = "missed_event"
            description = "Addiction caused you to miss an important event."

        assert event_type in ADDICTION_EVENTS

        event = RandomEvent(
            id=None,
            band_id=None,
            avatar_id=user_id,
            type=event_type,
            description=description,
        )
        if self.db:
            self.db.insert_random_event(event)
        self._apply_impact(event)
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
