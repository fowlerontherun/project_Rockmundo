
from datetime import datetime

class TourRoute:
    def __init__(self, id, band_id, vehicle_id, origin, destination, departure, arrival, cost, fatigue_impact, event_id=None):
        self.id = id
        self.band_id = band_id
        self.vehicle_id = vehicle_id
        self.origin = origin
        self.destination = destination
        self.departure = departure
        self.arrival = arrival
        self.cost = cost
        self.fatigue_impact = fatigue_impact
        self.event_id = event_id

    def to_dict(self):
        return self.__dict__
