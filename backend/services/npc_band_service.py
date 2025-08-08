
from models.npc_band import NPCBand
from datetime import datetime, timedelta
import random

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
            self.db.record_npc_event(band_id, f"Gained {fame_gain} fame from a simulated event")
