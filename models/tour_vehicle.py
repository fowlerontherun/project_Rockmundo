
from datetime import datetime

class TourVehicle:
    def __init__(self, id, band_id, type, capacity, perks, condition=100, mileage=0, last_service=None):
        self.id = id
        self.band_id = band_id
        self.type = type  # e.g., 'van', 'bus', 'plane'
        self.capacity = capacity
        self.perks = perks  # e.g., 'merch_shop', 'sleep_pods'
        self.condition = condition
        self.mileage = mileage
        self.last_service = last_service or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
