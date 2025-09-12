
from models.tour_vehicle import TourVehicle
from models.tour_route import TourRoute
from datetime import datetime, timedelta
import random

from backend.services.transport_service import TransportService

class TourLogisticsService:
    def __init__(self, db, transport: TransportService | None = None):
        self.db = db
        self.transport = transport or TransportService(db)

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

        vehicle_type = "van"
        try:
            vehicle = self.db.get_vehicle(vehicle_id)
            vehicle_type = getattr(vehicle, "type", vehicle_type)
        except Exception:
            pass
        disruption_info = self.check_disruptions(vehicle_type, origin, destination)
        data = route.to_dict()
        data.update(disruption_info)
        return data

    def get_band_routes(self, band_id):
        return self.db.get_routes_by_band(band_id)

    def get_band_vehicles(self, band_id):
        return self.db.get_vehicles_by_band(band_id)

    def check_disruptions(self, vehicle_type, origin, destination, weather="clear"):
        risks = self.transport.evaluate_risks(vehicle_type, weather)
        options = []
        if "mechanical_issue" in risks:
            options.extend(["repair_vehicle", "hire_replacement"])
        if "traffic_jam" in risks:
            options.extend(["wait_it_out", "take_detour"])
        if "weather_delay" in risks:
            options.extend(["delay_departure", "change_route"])
        return {"disruptions": risks, "options": options}
