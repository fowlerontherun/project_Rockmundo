
from models.transport import Transport
from datetime import datetime
import random

DEFAULT_VEHICLE_STATS = {
    "van": {"speed": 80, "fatigue_rate": 1.2, "capacity": 4, "perks": []},
    "bus": {"speed": 70, "fatigue_rate": 0.8, "capacity": 10, "perks": ["sleeping_pods"]},
    "truck": {"speed": 60, "fatigue_rate": 1.5, "capacity": 6, "perks": ["merch_storage"]},
    "plane": {"speed": 500, "fatigue_rate": 2.5, "capacity": 5, "perks": ["fast_travel"]},
    "ferry": {"speed": 40, "fatigue_rate": 1.0, "capacity": 6, "perks": []},
}

class TransportService:
    def __init__(self, db):
        self.db = db

    def assign_vehicle(self, band_id, vehicle_type):
        stats = DEFAULT_VEHICLE_STATS[vehicle_type]
        vehicle = Transport(
            id=None,
            band_id=band_id,
            vehicle_type=vehicle_type,
            speed=stats["speed"],
            fatigue_rate=stats["fatigue_rate"],
            capacity=stats["capacity"],
            perks=stats["perks"]
        )
        self.db.insert_transport(vehicle)
        return vehicle.to_dict()

    def get_band_vehicle(self, band_id):
        return self.db.get_transport_by_band(band_id)

    def update_maintenance(self, vehicle_id):
        self.db.update_transport_maintenance(vehicle_id, datetime.utcnow().isoformat())

    def evaluate_risks(self, vehicle_type, weather="clear"):
        """Simple travel risk assessment.

        Returns a list of potential disruptions based on vehicle type and
        ambient weather. Probabilities are intentionally light-weight for
        demonstration and tests.
        """
        risks = []
        if random.random() < 0.1:
            risks.append("traffic_jam")
        if vehicle_type in ("van", "bus", "truck") and random.random() < 0.05:
            risks.append("mechanical_issue")
        if weather in ("storm", "snow") and random.random() < 0.3:
            risks.append("weather_delay")
        return risks
