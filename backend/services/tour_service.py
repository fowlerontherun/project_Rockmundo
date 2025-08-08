
from models.tour import Tour
from datetime import datetime

class TourService:
    def __init__(self, db):
        self.db = db

    def create_tour(self, data):
        if len(data['route']) < 2:
            raise ValueError("Tour must include at least two cities.")
        tour = Tour(**data)
        self.db.insert_tour(tour)
        return tour.to_dict()

    def list_tours_by_band(self, band_id):
        return self.db.get_tours_by_band(band_id)

    def update_tour_status(self, tour_id, status):
        self.db.update_tour_status(tour_id, status)

    def get_tour(self, tour_id):
        return self.db.get_tour_by_id(tour_id)
