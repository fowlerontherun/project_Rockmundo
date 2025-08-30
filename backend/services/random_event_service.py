import random

from seeds.skill_seed import SKILL_NAME_TO_ID

from backend.models.random_event import RandomEvent
from backend.models.skill import Skill
from backend.services.skill_service import skill_service


class RandomEventService:
    def __init__(self, db):
        self.db = db

    def trigger_event_for_band(self, band_id):
        options = [
            ("delay", "Vehicle breakdown caused a delay.", "fatigue +5"),
            ("press", "Local press covered the band’s arrival.", "fame +10"),
            ("fan_interaction", "Fans welcomed the band at the venue.", "funds +50")
        ]
        selected = random.choice(options)
        event = RandomEvent(
            id=None,
            band_id=band_id,
            type=selected[0],
            description=selected[1],
            impact=selected[2]
        )
        self.db.insert_random_event(event)
        self._apply_impact(band_id, selected[2])
        return event.to_dict()

    def _apply_impact(self, band_id, impact_str):
        if "fame" in impact_str:
            value = int(impact_str.split("+")[1])
            self.db.increase_band_fame(band_id, value)
        elif "funds" in impact_str:
            value = int(impact_str.split("+")[1])
            self.db.increase_band_funds(band_id, value)
        elif "fatigue" in impact_str:
            value = int(impact_str.split("+")[1])
            self.db.increase_band_fatigue(band_id, value)
        elif "skill" in impact_str:
            # Format: "skill:guitar +5" or "skill:drums -3"
            try:
                skill_part, value_part = impact_str.split()
                skill_name = skill_part.split(":", 1)[1]
                amount = int(value_part)
            except Exception:
                return
            skill_id = SKILL_NAME_TO_ID.get(skill_name)
            if skill_id is None:
                return
            if amount >= 0:
                skill_service.train(
                    band_id,
                    Skill(id=skill_id, name=skill_name, category="event"),
                    amount,
                )
            else:
                skill_service.apply_decay(band_id, skill_id, -amount)
