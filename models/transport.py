
from datetime import datetime

class Transport:
    def __init__(self, id, band_id, vehicle_type, speed, fatigue_rate, capacity, perks, last_maintenance=None):
        self.id = id
        self.band_id = band_id
        self.vehicle_type = vehicle_type  # van, bus, truck, plane, ferry
        self.speed = speed  # km/h
        self.fatigue_rate = fatigue_rate  # fatigue per hour
        self.capacity = capacity  # seats or load
        self.perks = perks or []
        self.last_maintenance = last_maintenance or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
