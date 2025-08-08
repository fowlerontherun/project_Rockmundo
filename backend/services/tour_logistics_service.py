
from models.tour_vehicle import TourVehicle
from models.tour_route import TourRoute
from datetime import datetime, timedelta
import random

class TourLogisticsService:
    def __init__(self, db):
        self.db = db

    def register_vehicle(self, band_id, type, capacity, perks):
        vehicle = TourVehicle(id=None, band_id=band_id, type=type, capacity=capacity, perks=perks)
        self.db.insert_tour_vehicle(vehicle)
        return vehicle.to_dict()

    def plan_route(self, band_id, vehicle_id, origin, destination, hours, cost):
        fatigue = random.randint(5, 20)
        now = datetime.utcnow()
        route = TourRoute(
            id=None,
            band_id=band_id,
            vehicle_id=vehicle_id,
            origin=origin,
            destination=destination,
            departure=now.isoformat(),
            arrival=(now + timedelta(hours=hours)).isoformat(),
            cost=cost,
            fatigue_impact=fatigue
        )
        self.db.insert_tour_route(route)
        self.db.deduct_band_funds(band_id, cost)
        self.db.increase_band_fatigue(band_id, fatigue)
        self.db.add_mileage(vehicle_id, hours * 50)
        return route.to_dict()

    def get_band_routes(self, band_id):
        return self.db.get_routes_by_band(band_id)

    def get_band_vehicles(self, band_id):
        return self.db.get_vehicles_by_band(band_id)
