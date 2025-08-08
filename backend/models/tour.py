
from datetime import datetime

class Tour:
    def __init__(self, id, band_id, title, start_date, end_date, route, vehicle_type, status='planned'):
        self.id = id
        self.band_id = band_id
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.route = route  # list of cities
        self.vehicle_type = vehicle_type  # van, bus, truck, plane
        self.status = status  # planned, active, completed
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
