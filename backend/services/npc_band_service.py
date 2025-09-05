
from models.npc_band import NPCBand
from datetime import datetime, timedelta
import random

try:  # pragma: no cover - import path shim
    from services.world_pulse_service import get_current_season
except Exception:  # pragma: no cover
    from backend.services.world_pulse_service import get_current_season

class NPCBandService:
    def __init__(self, db):
        self.db = db

    def create_npc_band(self, name, genre):
        band = NPCBand(
            id=None,
            name=name,
            genre=genre,
            activity_level=random.randint(1, 5),
            fame=random.randint(10, 100)
        )
        self.db.insert_npc_band(band)
        return band.to_dict()

    def run_simulation_loop(self):
        npc_bands = self.db.get_all_npc_bands()
        for band in npc_bands:
            band_id = band["id"]
            fame_gain = random.randint(0, band["activity_level"])
            self.db.increase_npc_fame(band_id, fame_gain)
            self.db.record_npc_event(
                band_id, f"Gained {fame_gain} fame from a simulated event"
            )

            # Occasionally schedule a seasonal gig or release
            if random.random() < 0.3:
                self.schedule_seasonal_activity(band_id)

    def schedule_seasonal_activity(self, band_id: int) -> dict:
        """Plan a seasonal gig or release for an NPC band.

        The activity type is chosen at random and scheduled within the next
        ninety days. A corresponding event is persisted via ``record_npc_event``.
        """

        season = get_current_season()
        activity = random.choice(["gig", "release"])
        date = datetime.utcnow() + timedelta(days=random.randint(1, 90))
        description = (
            f"Scheduled {activity} for the {season} season on {date.date().isoformat()}"
        )
        self.db.record_npc_event(band_id, description)
        return {
            "band_id": band_id,
            "activity": activity,
            "season": season,
            "date": date.date().isoformat(),
        }
